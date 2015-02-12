=head1 NAME

Beginnerprise::Mysql - Standard Beginnerprise Mysql Tooset for Perl

=cut

#######################################################################
## 
## Authors:	Benjamin Hudgens
## Date:	December 14, 2006
## Modified:	February 2, 2009 - Modify how the debug messages behave
## Modified:	May 9, 2012 - Modify how the debug messages behave again
## 
## 
## Beginnerprise Mysql Wrapper library
## 
## Functions to simplify the usage of the beginnerprise database from perl
##
#######################################################################

package Beginnerprise::Mysql;

## Required for all beginnerprise perl code
use Beginnerprise::Standard;

use Exporter qw(import);
use DBI;

@EXPORT    = qw ( dbConnect
		  dbUpdate
		  dbWrite
		  dbRead
		  dbQuery
		  dbDisconnect );

=head1 SYNOPSIS

    my $query = "SELECT (...)";
    dbRead($query);

    my $query = "INSERT (...)";
    dbWrite(query);

    my $query = "UPDATE (...)";
    dbWrite($query);

=cut

######################################################################
## Global Configuration
######################################################################

my $dbhRead	= undef;
my $dbhWrite	= undef;

my $db_username	= 'beginnerprise';
my $db_password	= 'password';  # Set to a default password for ease of use
my $db_server	= 'db.beginnerprise.com';
my $db_name	= 'beginnerprise';


=head1 DESCRIPTION

The Beginnerprise::Mysql module is intended to simply communicating with the Beginnerprise Mysql databases.  Using these routines should ensure that you make queries against the proper databases and protect against accidental insert with the wrong databases.  There are also
a number of helper routines to minimize the overhead of working with DBI.  

=head2 dbConnect()

Used to connect to the default read/write database.  Additionally use can pass arguments to specify login information

    Example:

	my $dbh	= &dbConnect();

    or

	my $dbh = &dbConnect($dbServer,$dbName,$dbUsername,$dbPassword);

    Usage:	$dbh = dbConnect()

		$dbh is the returned database handler from this method
	      
                You can pass the following:
                  server
                  name
                  username
                  password

                Leaving any of the entries blank will use the defaults

    Returns:    DBI database handle; undef on failure and sets 
		soft error to true

=cut

sub dbConnect {


    my $chk		= @_;

    if ($chk == 4)
    {

        $db_server   = shift;
	$db_name     = shift;
	$db_username = shift;
	$db_password = shift;

    }

    my $check		= undef;
    my $return		= undef;

    &debug(101,"Connecting to Mysql...");
    &debug(102,"Mysql Server: $db_server");
    &debug(102,"Username:     $db_username");
    &debug(109,"Password:     $db_password");

    ## Create a new LDAP Object
    $return = DBI->connect("dbi:mysql:dbname=$db_name;host=$db_server",$db_username,$db_password) 
	    || &sError("$DBI::errstr");

    ## Try to connect with the credentials

    return($return);

}

=head2 dbRead()

Used to run SELECT queries against the Beginnerprise Mysql servers.  If a connection has not been made to the database it will automatically handle making connections for you.  The results are always returned as a ptr to an array.  The array consists of ptrs to column values.

It's important to note that read servers are sometimes behind.  They may not always contain information about a write that was just acted on.  In those cases where you need immediate access to data that was just inserted you may need to use L<dbQuery>.

    Example:

	my $results = dbRead("SELECT * from table");

	foreach my $result (@{$results})
	{
	    print $result->[$columnId]; # starts at 0 from the first item in your column list of the select statement
	}

    Usage:	$resultsRef = dbRead($sqlQuery)

		$resultsRef is a pointer to an array of rows 

		$sqlQuery is the query to run against db

    Returns:	Returns results pointer | undef with error

=cut

sub dbRead {

    my $sqlQuery 	= shift;

    if (!$dbhRead)
    {
	$dbhRead	= &dbConnect("dbread.beginnerprise.com","beginnerprise","beginnerprise","password");
    }

    my $return = &dbQuery($dbhRead,$sqlQuery);


    return($return);

}

=head2 dbWrite()

Used to run UPDATE and INSERT statements against the Beginnerprise Write Mysql Servers.  If a connection has not been made to the database it will automatically handle making connections for you. 

    Example:

	my $id = dbWrite("INSERT INTO (...)");

	dbWrite("UPDATE (...)");

	if (getErrorStatus())
	{
	    # We had an error
	}

    Usage:	my $id dbWrite($sqlQuery)

	        $sqlQuery is the query to run against db

    Returns:	(No Return Value on update),Sets sError on Error,Returns record id on insert

=cut

sub dbWrite {

    my $sqlQuery 	= shift;

    if (!$dbhWrite)
    {
	$dbhWrite	= &dbConnect("dbwrite.beginnerprise.com","beginnerprise","beginnerprise","password");
    }

    my $return = &dbUpdate($dbhWrite,$sqlQuery);


    return($return);

}

=head2 dbQuery()

Used to run SELECT statements against the $dbh passed.  The results are always returned as a ptr to an array.  The array consists of ptrs to column values.

    Example:

	my $results = dbQuery($dbh,"SELECT * from table");

	foreach my $result (@{$results})
	{
	    print $result->[$columnId]; # starts at 0 from the first item in your column list of the select statement
	}

    Usage:	$resultsRef = dbQuery($dbh,$sqlQuery)

		$resultsRef is a pointer to an array of rows 
		each row is an array pointer of search results

		$sqlQuery is the query to run against db

    Returns:	Returns results pointer

=cut 

sub dbQuery {

    my $dh		= shift;
    my $sqlQuery 	= shift;

    my $sh		= undef;
    my $return		= undef;
    my $chk		= undef;

    &debug(101,"Running DB Query: ");
    &debug(102,"$sqlQuery");

    if ($sqlQuery !~ /\s*select/i)
    {
	&sError("Non-Select Query Sent to Read Server");
	return(undef);
    }

    $sh			= $dh->prepare($sqlQuery);
    $chk = $sh->execute();

    if (!$chk) {
        &sError("Query Failed: $DBI::errstr");
	return(undef);
    }

    $return = $sh->fetchall_arrayref;

    return($return);

}

=head2 dbUpdate()

Use to send INSERTS and UPDATES to $dbh Mysql connection

    Usage:	dbQuery($dbh,$sqlQuery)

		$sqlQuery is the query to run against db

    Returns:	(No Return Value),Sets sError on Error

=cut

sub dbUpdate {

    my $dh		= shift;
    my $sqlQuery 	= shift;

    my $sh		= undef;
    my $chk		= undef;
    my $insertId	= undef;

    if (!$sqlQuery || !$dh)
    {
	&sError("Must send valid dbHandle and Query string");
	return(undef);
    }

    &debug(101,"Running DB Update: $sqlQuery");

    if ($sqlQuery !~ /\s*insert/i && $sqlQuery !~ /\s*update/i)
    {
	&sError("Non-Insert or Non-Update Query Sent to Write Server");
	return(undef);
    }

    $sh			= $dh->prepare($sqlQuery);
    $chk = $sh->execute;

    if (!$chk) {
        &sError("Query Failed: $DBI::errstr");
	return(undef);
    }

    if ($sqlQuery =~ /^\s*insert.*/i) {
        $insertId		= $dh->last_insert_id(undef,undef,undef,undef);
	return($insertId);
    }

    return(undef);

}

=head2 dbDisconnect()

Use to disconnect the db handle passed to us

    Usage:	dbDisconnect($dbh);

		$dbh an open db handle to be closed

    Returns:	(No Return Value)

=cut

sub dbDisconnect {

    my $dh 		= shift;

    debug(101,"Closing DB connection");

    if ($dh)
    {
	$dh->disconnect();
    }

    return();

}

1;

=pod 

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

=cut


