#! /usr/bin/perl

##
# THIS IS A TOTAL HACK JOB TO WHACK SOMETHING TOGETHER TO HELP US ROLE OUT PHONES
#
# DO NOT JUDGE.. BLAZED THROUGH THIS TO GET IT OUT
#
# SHOULD BE CLEANED UP .. AWFUL

use CGI;
use Beginnerprise::Standard;
use MIME::Entity;
use IO::Socket;
use JSON;
use XML::Simple;

my $q			= new CGI;
my $xml 		= new XML::Simple;
my @finalEmailText	= ();
my $toAddress		= 'internalsupport@bpok.com';
my $fromAddress		= 'asterisk@bpok.com';
my $subject		= 'Polycom Web Interface Support Request';
my $sendmail		= '/usr/sbin/sendmail';
my $ami_username	= 'admin';
my $ami_password	= 'amp111';
my $params		= {};
# Default Response Type
my $responseType	= 'xml';

sub main ()
{
  if ( $q->param() > 0 )
  {
    if ( $q->param('command') eq "support")
    {
      my $body = "";

      $body .= '><br/>' . "\n";
      $body .= '><br/>' . "\n";
      $body .= 'Your Request Has Been Submitted!' . "\n";

      &doOutput($body);
      &buildEmail();
      &sendEmail();

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


        $msg = &ami_command($cmd);

        $response->{'response'}->{'code'}		= 200;
        $response->{'response'}->{'message'}	= "Call Sent";
        return;
      }

      ## If we get here then a valid command wasn't found
      $response->{'error'}->{'code'}              = 500;
      $response->{'error'}->{'message'}           = "Command Not Found";
    }
    else
    {
    }

  }
  else
  {
    my %nm;
    my $cmd 	= undef;

    $cmd 	.= "Action: GetVar\r\n";
    $cmd 	.= "Variable: NIGHTMODE\r\n";
    $cmd 	.= "\r\n";

    my $response = &ami_command($cmd);

    if ($response =~ /.*Value:\s(.*?)\r\n/)
    {
      $nm{'bp'} = $1;
    }
    exit(0);

    my $body = "";

    $body .= '><br/>' . "\n";
    $body .= '><br/>' . "\n";
    $body .= '<a href="http://phones1.bp.local/cgi-bin/phoneapp.cgi?command=support">I need phone help</a>' . "\n";

    &doOutput($body);
  }

}


sub doOutput()
{
  my $body = shift;

  print $q->header();
  print <<"  EOF";
  <html>
  <head>
  <title>Phone Application</title>
  </head>
  <body>
  $body
  </body>
  </html>
  EOF

}

sub shutdown()
{
  exit( $_[0] );
}

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

  my $response = undef;

  while (<$ami>)
  {
    $response .= $_;
  }

  return $response;

}

sub sendEmail {

  my $mimeObject      = undef;

  open(SENDMAIL,"| $sendmail -t -oi -oem");

  $mimeObject         = MIME::Entity->build(Type      => 'multipart/alternative',
  From      => "$fromAddress",
  To        => "$toAddress",
  Subject   => "$subject",
  Encoding  => '8bit'
  );

  $mimeObject->attach(
  Data    =>      [@finalEmailText],
  Type    =>      'text/plain',
  Charset =>      'iso-8859-1',
  Filename=>      undef,
  Encoding=>      'quoted-printable'
  );

  $mimeObject->print(\*SENDMAIL);
  close(SENDMAIL);

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

sub buildEmail
{
  my $body = "";

  my $ipaddress	= $ENV{'REMOTE_ADDR'};
  my @arps 		= `/usr/sbin/arp -an | grep $ipaddress`;
  foreach my $arp (@arps)
  {
    if ($arp =~ /.*$ipaddress.*at\s(.*)\s\[et.*$/)
    {
      $macaddress = $1;
      last;
    }
  }

  $macaddress =~ s/://g;
  $macaddress = lc($macaddress);

  my @lines 	= ();

  if (-f "/tftpboot/$macaddress-phone.cfg")
  {
    open(IN,"< /tftpboot/$macaddress-phone.cfg");
    @lines = <IN>;
    close(IN);
  }

  my $extension 	= undef;
  my $name 		= undef;

  foreach my $line (@lines)
  {
    if ($line =~ /displayName=\"(.*)\".*$/)
    {
      $name = $1;
    }
    if ($line =~ /reg.1.address=\"(.*)\".*$/)
    {
      $extension = $1;
    }
  }

  push(@finalEmailText,"\n");
  push(@finalEmailText,"\n");
  push(@finalEmailText,"Support Requested From User\n");
  push(@finalEmailText,"---------------------------------\n");
  push(@finalEmailText,"Username:  $name\n");
  push(@finalEmailText,"Extension: $extension\n");
  push(@finalEmailText,"Phone IP:  $ipaddress\n");
  push(@finalEmailText,"Phone MAC: $macaddress\n");
  push(@finalEmailText,"\n");
  push(@finalEmailText,"\n");

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

&main();
exit(0);
