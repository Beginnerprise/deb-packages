#!/usr/bin/perl

my $dir = '/usr/local/src/bp-perl-modules';
chdir($dir);

my $cmd = 'perl Makefile.PL';
system($cmd);

my $cmd = 'make';
system($cmd);

my $cmd = 'make install';
system($cmd);

exit(0); 
