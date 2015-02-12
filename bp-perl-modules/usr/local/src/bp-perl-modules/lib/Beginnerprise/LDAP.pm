#######################################################################
## 
## Authors:	Benjamin Hudgens
## Date:	November 15, 2006
## Modified:	May 9, 2012
## 
## 
## Beginnerprise LDAP Wrapper library
## 
## Functions to simplify the usage of Active Directory from perl
## At beginnerprise
#######################################################################

package Beginnerprise::LDAP;

## Required for all Beginnerprise perl code
use Beginnerprise::Standard;

use Exporter qw(import);
use Net::LDAP;

@EXPORT    = qw ( openLDAPConnection 
		  searchLDAP
		  closeLDAPConnection );


#######################################################################
## Method:  	openLDAPConnection
##
## Usage:	openLDAPConnection($ldap_database,$username,$password)
##
##		$ldap_database is the server name or ip address
##		$username is the username to login with
##		$password is the password to login with
##
## Returns:	Net::LDAP object
#######################################################################

sub openLDAPConnection {

   my $ldapserver	= shift;
   my $username		= shift;
   my $password		= shift;

   my $check		= undef;
   my $return		= undef;

   &debug(101,"Connecting to LDAP...");
   &debug(102,"Ldap Server: $ldapserver");
   &debug(102,"Username:    $username");
   &debug(109,"Password:    $password");

   if (!$ldapserver) { &sError("openLDAPConnection: LDAP Server not specified")   };
   if (!$username)   { &sError("openLDAPConnection: LDAP username not specified") };
   if (!$password)   { &sError("openLDAPConnection: LDAP password not specified") };

   ## Create a new LDAP Object
   $return = Net::LDAP->new($ldapserver) 
				|| &sError("Couldn't Connect to Domain Controller");

   ## Try to connect with the credentials
   $result = $return->bind( $username, password => $password);

   if ($result->code()) { &sError("Connection to LDAP Server Failed:  $result->code()") };

   return($return);

}

#######################################################################
## Method:  	searchLDAP
##
## Usage:	searchLDAP($ldap_object,$search_array_reference)
##
##		$ldap_object an ldap connection object 
##			     (see openLDAPConnection)
##		$search_array_ref reference to an array of search 
##				  criteria.  See man page for Net::LDAP
##
## Returns:	Reference to an array of Net::LDAP::Entries
#######################################################################

sub searchLDAP {

    my $ldapobject 	= shift;
    my $sar 		= shift;
    my $return		= undef;
    my @res		= ();

    # Define search criteria
    @search             = @$sar;

    # Execute search and collect results
    $mesgObject = $ldapobject->search(@search);

    @res = $mesgObject->entries;

    ## Convert Results to pointer
    $return = \@res;

    return($return);

}

#######################################################################
## Method:  	closeLDAPConnection
##
## Usage:	closeLDAPConnection($ldap_object);
##
##		$ldap_object an ldap connection object 
##			     (see openLDAPConnection)
##
## Returns:	(No Return Value)
#######################################################################

sub closeLDAPConnection {

    my $ldapObject = shift;

    debug(101,"Closing ldap connection");

    $ldapObject->unbind();

    $ldapObject = undef;

    return();

}

1;
