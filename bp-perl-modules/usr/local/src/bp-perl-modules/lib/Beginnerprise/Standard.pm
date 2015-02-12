=head1 NAME

Beginnerprise::Standard - Standard Beginnerprise Toolset for Perl

=cut

#########################################################################################
##
## Authors:     Benjamin Hudgens
## Date:        November 15, 2006
## Modified:    May 9, 2012 - Changed debug message values/added debug Timestamps
##
## Beginnerprise Standard Error and IO handling
##
## Functions to standardize the look and feel of beginnerprise perl code
#########################################################################################

=head1 SYNOPSIS

Configure Debugging

    setDebugLevel($level);
    setDebugEnableTimeStamp(1);
    setDebugLogFile($optional_log_file);

Use Debugging

    debug($level,$message); 

Print STDOUT

    say($message_to_STDOUT);

Saving data blobs

    saveConfig($file,$hashRef);
    $hashRef = readConfig($file);

Handling Command Line Args (@ARGV)

    my $opts = getCommandLineOptions($options);

Run as a daemon

    daemonize(); 

Soft Errors

    sError($optional_reason_for_error)

    if (getErrorStatus())
    {
	my $error = &getErrorStatus();
	say($error);
	resetErrorStatus();
    }

Hard or Halt Errors

    hError($reason_to_hault_execution)


Get a child process

    my $pid = getChild();

    if (!getErrorStatus()) {
	if ($pid) {
	    ..parent
	} else {
	    ..child
	}
    } else {
	..error
    }

=head1 DESCRIPTION

The Beginnerprise::Standard module is intended to unify common code routines amongs all the Beginnerprise scripts.  It is a list of helper routines that are intended to always perform the same.  Instead of retyping the same code in each script we throw these routines in here.

See L<EXAMPLES> for an example of all functions in this library

=cut

package Beginnerprise::Standard;

use Exporter qw(import);

## Version
$VERSION 	= '2.01';

## Export these functions

@EXPORT		= qw (
		      debug 
		      say 
		      setDebugLevel
		      setDebugLogFile
		      setDebugEnableTimeStamp
		      sError
		      hError
		      saveConfig
		      readConfig
		      getCommandLineOptions
		      resetErrorStatus
		      getErrorStatus
		      daemonize
		      getChild
		     );

my $debug 			= 0;
my $logToFile			= undef;
my $logFile			= undef;
my $isError			= undef;
my $isDebugTimeStampEnabled	= undef;

=pod 

=head2 setDebugEnableTimeStamp()

Enables or Disables prepending Time-Stamps to the debug output statements.  The default is off.

    Usage: 	setDebugEnableTimeStamp(0|1)
    Returns: 	(No Return Value)

=cut

sub setDebugEnableTimeStamp {

   $isDebugTimeStampEnabled = shift;

}

=pod 

=head2 setDebugLevel()

This sets what level debug output messages will be displayed.  The default is 0.

    Usage:       setDebugLevel($value);
    Returns:     (No Return Value)

=cut

sub setDebugLevel {

   my $lvl = shift;

   if ($lvl > 0) { 
       $debug = $lvl;
   }

}

=pod 

=head2 setDebugLogFile()

Creates an output file and dumps debug messages to that file instead of STDOUT

    Usage:      setDebugLogFile($value);
    Returns:    (No Return Value)

=cut

sub setDebugLogFile {

   my $lf = shift;

   `touch $lf`;
   if (!-f $lf) { &sError("Couldn't create logfile") };

   $logToFile = 1;
   $logFile = $lf;

}

=pod 

=head2 getCommandLineOptions()

    Grabs and parses command line options.  You pass a string of letters as $options.
    The form is a single letter or a single letter followed by a collon (:).
    
    Example:  
    	my $options = 'ab:'

	my $opts = getCommandLineOptions($options)

	if ($opts->{'a'}) # boolean check for this argument in ARGV
	if ($opts->{'b'} eq "test") # pass -b <option> at the command line.  

    Usage:  	$opts = &getCommandLineOptions($options);

		$options - the command line options to return
			   (see man Getopt::Std)
		$opts -    is a hash reference to command line options
			   or null if there was an error

    Returns:    hashRef to arguments passed on command line

=cut

sub getCommandLineOptions
{

    &debug(101, "...sub getCommandLineOptions");

    use Getopt::Std;

    my $options		= shift;
    my %opts		= ();

    if (!$options) { 
        &debug(102, "Did not get options argument");
        return(undef);
    }

    my $chk     = getopts($options,\%opts);

    if (!$chk) { 
        &debug(102, "There was an error getting the returned options: $options");
        return(undef)
    }

    return(\%opts);

}

=pod

=head2 readConfig()

    Read a configuration file (XML) in as a hash of arrays.  We always read in using 
    arrays so we don't have to check if an element would be alone or in groups.

    Example:
	<root>
	    <nested>
		<foo>bar</foo>
	    </nested>
	    <nested>
		<fee>foe</fee>
	    </nested>
	</root>

    Would be read in like:

	$conf = readConfig($configFile);
	$conf->{'nested'}[0]->{'foo'}[0] <-- bar 
	$conf->{'nested'}[1]->{'fee'}[0] <-- foe 

    Usage:  	$config = readConfig($configFile);

    		$configFile is the file to read in

    Returns:    hashRef of the XML file read in

=cut

sub readConfig {

    #use XML::Dumper;

    use XML::Simple;

    my $cf      = shift;
    my $hr      = undef;
    #my $dumper  = undef;

    my $hr = XMLin($cf,ForceArray=>1);

    #$dumper     = new XML::Dumper;

    #if (!-f $cf) { &sError("readConfig could not find file: $cf") };

    #$hr         = $dumper->xml2pl($cf);

    return($hr);

}

=pod

=head2 saveConfig()

    saveConfig will save a hashRef as XML into a file.  Returns true if something went wrong.

    Usage:       saveConfig($configFile,$configHashRef);

		 $configFile is the file to save our config to

		 $configHashRef is the pointer to the data to save

    Returns:     undef is successful true if failed

=cut

sub saveConfig {

    use XML::Dumper;

    my $cf      = shift;
    my $hr      = shift;

    my $xml     = undef;
    my $cmd     = undef;
    #my $dumper  = undef;

    &debug(101,"sub saveConfig...");

    if (!-f $cf) {

        `touch $cf`;

        if (!-f $cf) {

            &sError("Couldn't create config file:  $cf");
            return(1);

        }

    }

    #$dumper     = new XML::Dumper;

    #$xml        = $dumper->pl2xml($hr);

    $xml 	= XMLout($hr,NoAttr=>1,RootName=>'config');

    open(OUT,"> $cf.tmp");
    print OUT $xml;
    close(OUT);

    $cmd        = "cp $cf.tmp $cf";
    &debug(109,"CMD: $cmd");
    system($cmd);

    $cmd        = "rm $cf.tmp";
    &debug(109,"CMD: $cmd");
    system($cmd);

    return(undef);

}

=pod

=head2 debug()

    Debug is used to insert helpful troubleshooting messages throughout your code.  You can 
    then control what gets shown and what is excluded by setting debug levels.  You can also
    specify that the messages to output to a file.  See L<setDebugLogFile>

    Usage:       debug($value,$message);

		 $value is the level of the debug message

		 $message is the debug message you want to produce

    Returns:     (No Return Value)

=cut

sub debug {

   my $lvl 		= shift;
   my $msg 		= shift;

   my $timeStamp 	= undef;

   if ($isDebugTimeStampEnabled)
   {
       my ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime(time);
       $mon    = $mon + 1;
       $year   = $year + 1900;
       $mon    = sprintf("%02d",$mon);
       $mday   = sprintf("%02d",$mday);
       $hour   = sprintf("%02d",$hour);
       $min    = sprintf("%02d",$min);
       $sec    = sprintf("%02d",$sec);

       $timeStamp = "$year-$mon-$mday $hour:$min:$sec\t"
   }

   $lvl = sprintf('%.2d',$lvl);

   if ($debug >= $lvl) {

       if ($logToFile) {
           open(OUT,">>$logFile");
           print OUT "$timeStamp" . "DEBUG[$lvl]: $msg\n";
	   close(OUT);
       } else {
           print "$timeStamp" . "DEBUG[$lvl]: $msg\n";
       }

   }

}

=head2 say()

Short hand to print a message to STDOUT

    Usage:       say($message);

                 $message is a message to print to the user

    Returns:     (No Return Value)

=cut

sub say {

    my $msg = shift;

    print "$msg\n";

}

=head2 hError()

Displays an error message to STDERR and exits.

    Usage:       hError($message);

                 $message is the output of the error

    Returns:     (No Return Value)

=cut

sub hError {

    my $msg = shift;
   
    print STDERR "\nERROR: $msg\n\n";
    exit(1);

}

=head2 sError()

Used to set us in an Error state but not exit.  Simply flag an error and
keep going.  The error state stays constant until reset

    Usage:       sError($message);

                 $message is the output of the error

    Returns:     Calling sError sets isError to true

=cut

sub sError {

    my $msg = shift;
    
    if ($msg)
    {
	$isError = $msg;
    }
    else
    {
	$isError = 1;
    }
   
    print STDERR "\nERROR: $msg\n\n";

}

=head2 getErrorStatus()

If sError is called you can call this routine to return the error and test this routine for true

    Example:

	if (getErrorStatus())
	{
	    # We had an error
	}

    Usage:       $result = getErrorStatus;

    Returns:     True if an error occured; or returns the error message; false if no errors set

=cut

sub getErrorStatus {

    return($isError);

}

=head2 getChild()

Use to create child processes

    Example:

	my $pid = getChild();

	if (!getErrorStatus())
	{
	    if ($pid)
	    {
		#parent
	    }
	    else
	    {
		#child
	    }
	}

    Usage:  my $pid = getChild() 

    Returns: Process of child

=cut

sub getChild {

    use POSIX qw(setsid);

    my $pid	= undef;

    $pid = fork();

    if (!defined($pid))
    {
	&sError("Couldn't Fork");
	return(undef)
    } 
    elsif ($pid)
    {
        return($pid);
    }
    else
    {
        umask(0);
	setsid();
        return(0);
    }

}

=head2 daemonize()

    Daemonize will fork and start running the main thread in the background.  This should 
    be used somewhere at the very beginning of execution.  It's usually a good idea to 
    send debug logs to a file if you plan on using daemonize

    Usage:       daemonize()
    Returns:     (No Return Value)

=cut

sub daemonize {

   use POSIX qw(setsid);

   my $pid = undef; 
   chdir '/';
   umask 0;
   open (STDIN, '/dev/null');
   open (STDOUT, '/dev/null');
   open (STDERR, '/dev/null');
   if ($pid = fork())
   {
       exit(0);
   } 
   setsid();
   return(undef);
   
}

=head2 resetErrorStatus()

    Reset any flags set because we had an error or sError was called

    Usage:       resetErrorStatus();
    Returns:     (No Return Value)

=cut

sub resetErrorStatus {

    $isError = undef;
    return();

}

1;


=pod 

=head1 EXAMPLES

At some point we should write an entire example script

=begin later

use Beginnerprise::Standard;

daemonize();

my $opts = getCommandLineOptions('d');

if ($opts->{'d'}) {
    setDebugLevel($opts->{'d'});
    debug(1,"Debug Set to $opts->{'d'}"); 
}

=end later

=head1 COPYRIGHT

Copyright (C) 2012 Beginnerprise Corporation

Author:   Benjamin Hudgens

Date:     May 14, 2012

