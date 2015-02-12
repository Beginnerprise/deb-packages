#! /usr/bin/perl

###########################################################################
## Author:  		Benjamin Hudgens
## Date:    		February 9, 2014
##
## Description:		This is a super quick AGI script determine
##			the appropriate caller ID for someone
##			We cache a local xml file of all phones and
##			various details about those phones.  We then
##			look for the caller's extension and determine
##			what caller ID to assign
###########################################################################

use Beginnerprise::Standard;
use Beginnerprise::LDAP;
use Data::Dumper;
use strict;
$|=1;

## Domain Controller We want to connect to
my $domain                      = 'dc1.bp.local'; # We specifically specify a DC to avoid out-of-sync DC's from causing weird deployments
## Full Distinguished Name of the LDAP User we'll use to pull phone data
my $username                    = 'CN=Some User,OU=Users,DC=bp,DC=local';
## Password for AD User
my $password                    = '';
## Root DN to use for our search
my $baseDN                      = 'DC=bp,DC=local';

my $tmpPhonesFile		= '/tmp/tmpphones.xml';
my $opts			= {};
my %AGI				= ();
my $phones			= {};
my $callerid			= {};

$callerid->{'Beginnerprise'}		= '512-588-2342';
$callerid->{'default'}		= '512-588-2342';


sub main
{

  &initialize();

  # Check if cache file exists - if not - build it
  if (!-f $tmpPhonesFile)
  {
    &doBuildCacheFile();
  }

  # Load the cache file
  if (-f $tmpPhonesFile)
  {
    $phones = &readConfig($tmpPhonesFile)
  }

  # Check if Extension exists; if yes, get the company and set caller ID
  # If it does NOT exist then we will set caller ID to default
  my $callerExtension 	= $AGI{'callerid'};
  my $cmdToSend		= undef;

  foreach my $phone (keys $phones)
  {
    my $company = lc($phones->{$phone}[0]->{'company'}[0]);
    my $ucCompany = uc($company);

    if ($callerExtension == $phones->{$phone}[0]->{'extension'}[0])
    {
      if ($callerid->{$company})
      {
        $cmdToSend = "SET VARIABLE $ucCompany 1";
        &sendCommand($cmdToSend);
        &getResponse();
        $cmdToSend = "SET CALLERID \"$phones->{$phone}[0]->{'firstname'}[0] $phones->{$phone}[0]->{'lastname'}[0]\" <$callerid->{$company}>";
        last;
      }
    }
  }

  if (!$cmdToSend)
  {
    $cmdToSend = "SET CALLERID \"\" <$callerid->{'default'}>";
  }

  &sendCommand($cmdToSend);
  &getResponse();
}

sub doBuildCacheFile ()
{

  $phones = &getPhoneDataFromActiveDirectory();

  my $response = {};
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

  &saveConfig($tmpPhonesFile,$response);

  if (!-f $tmpPhonesFile)
  {
    #TODO:  Handle Errors Cleanly - Error!
    exit(1);
  }

}

sub getExtensions ()
{
  my @files = `ls /tftpboot/????????????-phone.cfg`;

  my @extensions	= ();

  foreach my $file (@files)
  {
    chomp($file);
    open(IN,"< $file");
    while(<IN>)
    {
      if ($_ =~ /address=\"(\d+)\"$/)
      {
        push(@extensions,$1);
        last;
      }
    }
    close(IN);
  }

  return(\@extensions);
}

sub sendCommand ()
{
  my $command = shift;
  print "$command\n";
}

sub getResponse ()
{
  my ($res) = @_;
  my $retval;
  chomp $res;
  if ($res =~ /^200/) {
    $res =~ /result=(-?\d+)/;
    if (!length($1)) {
      print STDERR "FAIL ($res)\n";
    } else {
      print STDERR "PASS ($1)\n";
    }
  } else {
    print STDERR "FAIL (unexpected result '$res')\n";
  }
}

# Read in our parameters
sub initialize ()
{
  while(<STDIN>) {
    chomp;
    if (!length($_))
    {
      last;
    }
    if (/^agi_(\w+)\:\s+(.*)$/) {
      $AGI{$1} = $2;
    }
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
  attrs   => ['givenName','sn','otherIpPhone','mail','company']
  );

  my $search = \@search;

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
        if ($skip) { next };

        if (!$phones->{$macaddress})
        {
          $phones->{$macaddress}->{'extension'}       = $extension;
          $phones->{$macaddress}->{'firstname'}       = $result->get_value('givenName');
          $phones->{$macaddress}->{'lastname'}        = $result->get_value('sn');
          $phones->{$macaddress}->{'email'}           = $result->get_value('mail');
          $phones->{$macaddress}->{'company'}         = $result->get_value('company');

          &debug(14,"FN: " . $phones->{$macaddress}->{'firstname'}  . " " .
          "LN: " . $phones->{$macaddress}->{'lastname'}  . " " .
          "EM: " . $phones->{$macaddress}->{'email'}  . " " .
          "HW: " . $macaddress . " " .
          "XT: " . $phones->{$macaddress}->{'extension'});
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


&main();
exit(0);
