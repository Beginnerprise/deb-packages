#! /usr/bin/perl

use IO::Socket;
use CGI;
use JSON;
use XML::Simple;

my $ami_username	= 'admin';
my $ami_password	= 'amp111';

my $q			= new CGI;
my $xml 		= new XML::Simple;
my $params		= {};
# Default Response Type
my $responseType	= 'xml';

sub ami_command {

  my $command 	= shift;

  my $cmd		= undef;

  $cmd 	.= "Action: Login\r\n";
  $cmd 	.= "Username: $ami_username\r\n";
  $cmd 	.= "Secret: $ami_password\r\n";
  $cmd 	.= "\r\n";
  $cmd 	.= "$command";
  $cmd 	.= "Action: Logoff\r\n";
  $cmd 	.= "\r\n";

  my $ami 		= IO::Socket::INET->new(PeerAddr=>'127.0.0.1',PeerPort=>5038,Proto=>'tcp') or die "failed to connect to AMI!";

  print $ami $cmd;

  while (<$ami>) {};

}

sub main ()
{
  if ( $q->param() > 0 )
  {
    &getParams();

    if ( !$params->{'command'} )
    {
      $response->{'error'}->{'code'}		= 500;
      $response->{'error'}->{'message'}		= "Did Not Provide a Command";
    }

    if ( $params->{'command'} =~ /call/i || $params->{'command'} =~ /dial/i)
    {

      my $source_extension	= $params->{'source_extension'};
      my $number_to_dial		= $params->{'number_to_dial'};
      my $caller_id		= $params->{'caller_id'};

      if ($source_extension eq "" || $number_to_dial eq "")
      {
        $response->{'error'}->{'code'}		= 500;
        $response->{'error'}->{'message'}	= "Must Provide Source Extension and Number to Dial";
        return;
      }

      if ($caller_id eq "")
      {
        $caller_id = "No Name <$source_extension>";
      }

      my $cmd 	= undef;

      $cmd 	.= "Action: Originate\r\n";
      $cmd 	.= "Channel: local/$source_extension\@main\r\n";
      $cmd 	.= "Exten: $number_to_dial\r\n";
      $cmd 	.= "CallerID: $source_extension\r\n";
      $cmd 	.= "Context: main\r\n";
      $cmd 	.= "Variable: INTERNALCALL=1\r\n";
      $cmd 	.= "Priority: 1\r\n";
      $cmd 	.= "\r\n";

      $msg = &ami_command($cmd);

      $response->{'response'}->{'code'}		= 200;
      $response->{'response'}->{'message'}	= "Call Sent";
      return;
    }

    ## If we get here then a valid command wasn't found
    $response->{'error'}->{'code'}              = 500;
    $response->{'error'}->{'message'}           = "Command Not Found";
  }
}

sub getParams ()
{
  my @_parms = $q->param();

  foreach my $_parm (@_parms)
  {
    $params->{$_parm} = $q->param($_parm);
  }

  if ( $params->{'responsetype'} )
  {
    $responseType = $params->{'responsetype'};
  }
}

sub doOutputResponse()
{
  if ( $responseType eq "xml" )
  {
    print "Content-Type:  text/xml\n\n";
    print $xml->XMLout( $response, NoAttr => 1, RootName => 'phone_api_response', XMLDecl => 1 );
  }

  if ( $responseType eq "json" )
  {
    print "Content-Type:  application/json\n\n";
    print encode_json($response);
  }

  if ( $responseType eq 'ascii' )
  {
    print "Content-Type:  text/ascii\n\n";
    print $response;
  }

  if ( $responseType eq 'file' )
  {
    open( OUT, ">/tmp/$$.file" );
    print OUT $response;
    close(OUT);
    &doSendFile( $responseFile, "/tmp/$$.file" );
    unlink("/tmp/$$.file");
  }

}

sub shutdown()
{
  exit( $_[0] );
}

&main();
&doOutputResponse();
&shutdown();
