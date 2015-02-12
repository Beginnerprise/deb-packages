#! /usr/bin/perl
#############################################################################################
## Author: 	Benjamin Hudgens
## Date:	  May 13, 2013
##
## Description:
##		Beginnerprise Phone List Generator
#############################################################################################

##### NOTE:  THIS IS A HACK JOB.  This should absolutely be broken out into raw HTML, JS, and this only respond to commands
#####        I fully acknowledge I did this in about an hour and it's awful

use CGI;
use Beginnerprise::Standard;
use Beginnerprise::LDAP;
use Data::Dumper;
use JSON;
use XML::Simple;

## Domain Controller We want to connect to
my $domain                      = ''; # We specifically specify a DC to avoid out-of-sync DC's from causing weird deployments
## Full Distinguished Name of the LDAP User we'll use to pull phone data
## Needs to be a full DN
my $username                    = '';
## Password for AD User
my $password                    = '';
## Root DN to use for our search
my $baseDN                      = 'DC=bp,DC=local';

my $q				= CGI->new();

my $xml               		= new XML::Simple;
my $params            		= {};
my $response          		= {};
my $responseType      		= "xml";


# Cleanly handle kill signal and shutdowns
$SIG{'TERM'}	= \&shutdown;

# Command line options
my $opts		= {};  # Always your command line args

sub main
{

  &initialize();

  if ( $q->param() > 0 )
  {

    &getParams();

    if ( $params->{'command'} =~ /getphones/i)
    {
      $phones = &getPhoneDataFromActiveDirectory();
      &doBuildResponseForPhones($phones);
    }
  }

}

sub doBuildResponseForPhones
{
  my $count = 0;
  foreach my $mac (%{$phones})
  {
    foreach my $key (keys %{$phones->{$mac}})
    {
      $response->{'phone' . $count}->{$key} = $phones->{$mac}->{$key};
      $response->{'phone' . $count}->{'mac'} = $mac;
    }
    $count++;
  }
}

sub getPhoneDataFromActiveDirectory
{
  &debug(11,"..sub getPhoneDataFromActiveDirectory");

  my $phones          = {};
  my $ldap = &openLDAPConnection($domain,$username,$password);

  my @search  =
  (
  base    => $baseDN,
  filter  => '(otherIpPhone=*)',
  #attrs   => ['givenName','sn','otherIpPhone','mail']
  );

  $search = \@search;

  my $results = &searchLDAP($ldap,$search);

  ## Debug Info
  if ($opts->{'d'})
  {
    my $count = @{$results};
    &debug(12,"Found $count object(s) with Phone Data");
  }
  &debug(999,"#### LDAP Search Results ####\n" . Dumper($results));

  foreach my $result (@{$results})
  {
    foreach my $phone ($result->get_value('otherIpPhone'))
    {
      my ($macaddress,$extension) = split(/\|/,$phone);

      if ($extension && $macaddress =~ /^([0-9A-F]{2}[:-]*){5}([0-9A-F]{2})$/i)
      {

        $macaddress =~ s/[:-]//g;
        $macaddress = lc($macaddress);

        # Sanity Check Extension
        my $skip = undef;
        foreach my $mac (keys %{$phones})
        {
          if ($phones->{$mac}->{'extension'} eq $extension)
          {
            my $err = "";
            $err .= "SKIPPED: Extension [$extension] for ";
            $err .= "[" . $result->get_value('givenName') . " " . $result->get_value('sn') . "]";
            $err .= " in use for ";
            $err .= "[$phones->{$mac}->{'firstname'} $phones->{$mac}->{'lastname'}]";
            &error($err);
            $skip = 1;
          }
        }
        if (!$result->get_value('mail'))
        {
          $skip = 1;
        }

        if ($skip) { next };

        if (!$phones->{$macaddress})
        {
          $phones->{$macaddress}->{'extension'}       = $extension;
          $phones->{$macaddress}->{'firstname'}       = $result->get_value('givenName');
          $phones->{$macaddress}->{'lastname'}        = $result->get_value('sn');
          $phones->{$macaddress}->{'email'}           = $result->get_value('mail');
          $phones->{$macaddress}->{'company'}         = $result->get_value('company');
        }
        else
        {
          my $err = "";
          $err .= "SKIPPED: Mac [$macaddress] for ";
          $err .= "[" . $result->get_value('givenName') . " " . $result->get_value('sn') . "]";
          $err .= " in use for ";
          $err .= "[$phones->{$macaddress}->{'firstname'} $phones->{$macaddress}->{'lastname'}]";
          &error($err);
        }
      }
      else
      {
        my $err = "";
        $err .= "SKIPPED: Malformed Phone Configuration [$phone] for ";
        $err .= $result->get_value('givenName') . " " . $result->get_value('sn');
        &error($err);
      }
    }
  }

  return($phones);
}

sub error
{
}


sub usage
{
  &say ("							");
  &say ("Beginnerprise Solutions Phone List Generator 	");
  &say ("Copyright (C) 2000-2014				");
  &say ("-------------------------------------------------");
  &say ("							");
  &say ("Usage:						");
  &say ("$0 [-h] [-d debuglevel]				");
  &say ("							");
  &say (" -d Set the Debug Level				");
  &say (" -h Display this help message			");
  &say ("							");
}

sub shutdown
{
  # We get called even if we are sent a kill()
  # Make sure to clean up 'anything' we are doing
  # We can get called at any time
  # Keep track of open files and various other things so they can get cleaned up

  exit(0);
}

sub initialize
{
  # Some standard opts
  # -d debug level
  # -g generate a config file
  # -h help summary

  $opts = &getCommandLineOptions('hd:'); # colon means takes argument / just letter is Boolean

  if (!$opts)   # We had an error
  {
    &usage();
    exit(0);
  }

  if ($opts->{'h'})
  {
    &usage();
    &shutdown();
  }

  if ($opts->{'d'})
  {
    &setDebugLevel($opts->{'d'});
    &debug(1,"Debug Level Set: $opts->{'d'}");
  }

}

sub doOutputResponse()
{
  if ( $responseType eq "xml" )
  {
    print "Content-Type:  text/xml\n\n";
    print $xml->XMLout( $response, NoAttr => 1, RootName => 'vpn_api_response', XMLDecl => 1 );
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

sub getParams()
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
&doOutputResponse();
&shutdown();
