#! /usr/bin/perl

use strict;
$|=1;

my %AGI		= ();

sub main
{
  #&initialize();

  my $extensions = &getExtensions();
  my $allphones = "";

  foreach my $extension (@{$extensions})
  {
    $allphones .= "sip/$extension\&";
  }
  chop($allphones);

  &sendCommand("EXEC Page \"$allphones\"");
  &getResponse();
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

&main();
exit(0);
