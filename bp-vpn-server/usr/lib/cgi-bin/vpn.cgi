#! /usr/bin/perl

###########################################################################################
##
## Author:	Benjamin Hudgens
## Date:	February 28, 2013
##
## Description:
## 		This is a quick API whipped together to support the VPN Client for 
##              SRN.  The entire code base was written in a few hours
##              Which is why it is sloppy and terrible.  If you re-use any of this code
##              then shame on you.  It is awful...
###########################################################################################

use CGI;
use JSON;
use XML::Simple;
use Net::LDAP;
use Net::LDAP::Constant ('LDAP_CONTROL_PAGED');
use Digest::HMAC_SHA1;
use Crypt::CBC;
use MIME::Base64;

import  Digest::HMAC_SHA1 qw(hmac_sha1);

my $CONFIG_PATH_USER_LOGIN = '/mnt/logon_tracker';
my $CONFIG_VPN_CLIENT_VERSION = '25';
my $CONFIG_DOMAIN_CONTROLLER = '192.168.0.53';
my $CONFIG_USER_KEY_PASSWORD = "d151515";
my $CONFIG_CYPHER_PASSWORD = 'kdjwe23';
my $CONFIG_CYPHER_SALT = 'hkdk23dw';
my $CONFIG_CYPHER_INITIAL_VECTOR = 'KDJowkERSD234jsn';
my $CONFIG_CYPHER_ITER = 1;
my $CONFIG_CYPHER_KEYLEN = 256/8;

my $c = new CGI;
my $xml = new XML::Simple;
my $params = {};
my $response = {};
my $responseType = "xml";
my $responseFile = "";
my $authenticatedUser = ();
my $user;
my $pass;

sub main 
{

    &doInitialize();

    if ($c->param() > 0)
    {
	&getParams();

	&debug('command',$params->{'command'} );
	#$params->{'key'} = 'GVp7v2dUMTTiKMqEm9iWuD4PAh2lgmLo787uAei/+uRhM1eF0IK/aVXdJYYa2dQvVHsJAbreJ4ebyzBRFuuCLISd2p/CLoNeCILX/1lOAv47Watk6eA4Hw4qjdg/ybQg';
	#$params->{'password'} = &encrypt("!b9bb9bb9b");

	if ($params->{'command'} =~ /auth/i)
	{
	    if (&isValidUser())
	    {
		$response->{'response'}->{'code'} = 200;
		$response->{'response'}->{'message'} = "User Is Valid";
		if (&isRDPPossible())
		{
		    $response->{'response'}->{'rdpenabled'} = "1";
		}
	    }
	    else
	    {
		$response->{'error'}->{'code'} = 500;
		$response->{'error'}->{'message'} = "Invalid User";
	    }
	}
	else
	{
	    ##########################################
	    ## Handle all the commands
	    ##########################################
	    if (&isValidUser())
	    {
		if ($params->{'command'} =~ /vpnconfig/i)
		{
		    $response = undef;

		    $response .= "client\r\n";
		    $response .= "dev tun\r\n";
		    $response .= "proto tcp\r\n";
		    $response .= "remote 66.210.189.134 995\r\n";
		    $response .= "resolv-retry infinite\r\n";
		    $response .= "nobind\r\n";
		    $response .= "persist-key\r\n";
		    $response .= "persist-tun\r\n";
		    $response .= "ca ca.crt\r\n";
		    $response .= "cert bp.crt\r\n";
		    $response .= "key bp.key\r\n";
		    $response .= "tun-mtu 1400\r\n";
		    $response .= "comp-lzo\r\n";

		    $responseType='ascii';
		}

		if ($params->{'command'} =~ /fileusercert/i)
		{
		    my $path = '/etc/openvpn/easy-rsa/keys/user-' . $authenticatedUser->[3] . '.crt';

		    &doGenerateCertificates($authenticatedUser->[3]);
		    if (-f $path)
		    {
			&doSendFile('bp.crt',$path);
		    }
		}

		if ($params->{'command'} =~ /fileuserkey/i)
		{

		    my $path = '/etc/openvpn/easy-rsa/keys/user-' . $authenticatedUser->[3] . '.key';
		    &doGenerateCertificates();
		    if (-f $path)
		    {
			&doSendFile('bp.key',$path);
		    }
		}

		if ($params->{'command'} =~ /iphoneconfig/i)
		{

		    $responseType='ascii';

		    my $file = undef;

		    $response = undef;

		    $response .= "client\r\n";
		    $response .= "dev tun\r\n";
		    $response .= "proto tcp\r\n";
		    $response .= "remote 66.210.189.134 995\r\n";
		    $response .= "resolv-retry infinite\r\n";
		    $response .= "nobind\r\n";
		    $response .= "persist-key\r\n";
		    $response .= "persist-tun\r\n";
		    $response .= "ca ca.crt\r\n";
		    $response .= "cert bp.crt\r\n";
		    $response .= "key bp.key\r\n";
		    $response .= "tun-mtu 1400\r\n";
		    $response .= "comp-lzo\r\n";

		    $file = '/etc/openvpn/easy-rsa/keys/user-' . $authenticatedUser->[3] . '.crt';
		    $response .= "<cert>\r\n";
		    $response .= `cat '$file'`;
		    $response .= "</cert>\r\n";

		    $file = '/etc/openvpn/easy-rsa/keys/user-' . $authenticatedUser->[3] . '.key';
		    $response .= "<key>\r\n";
		    $response .= `cat '$file'`;
		    $response .= "</key>\r\n";
		    
		    $file = '/etc/openvpn/easy-rsa/keys/ca.crt';
		    $response .= "<cd>\r\n";
		    $response .= `cat '/etc/openvpn/easy-rsa/keys/ca.crt'`;
		    $response .= "</cd>\r\n";

		    my $tmpFile = "/tmp/$$-iphone.ovpn";

		    open(OUT,"> /tmp/$$-iphone.ovpn");
		    print OUT $response;
		    close(OUT);

		    &doSendFIle('bpvpn.ovpn',$tmpFile);


		}

		if ($params->{'command'} =~ /fileservercert/i)
		{
		    my $path = '/etc/openvpn/easy-rsa/keys/ca.crt';
		    if (-f $path)
		    {
			&doSendFile('ca.crt',$path);
		    }
		}


		if ( $params->{'command'} =~ /getrdp/i )
		{

			my $ip = &isRDPPossible();

			if ($ip)
			{

			    $response .= "screen mode id:i:2\r\n";
			    $response .= "use multimon:i:0\r\n";
			    $response .= "desktopwidth:i:1024\r\n";
			    $response .= "desktopheight:i:768\r\n";
			    $response .= "session bpp:i:16\r\n";
			    $response .= "winposstr:s:0,1,224,47,1920,927\r\n";
			    $response .= "compression:i:1\r\n";
			    $response .= "keyboardhook:i:2\r\n";
			    $response .= "audiocapturemode:i:0\r\n";
			    $response .= "videoplaybackmode:i:0\r\n";
			    $response .= "connection type:i:2\r\n";
			    $response .= "displayconnectionbar:i:1\r\n";
			    $response .= "disable wallpaper:i:1\r\n";
			    $response .= "allow font smoothing:i:0\r\n";
			    $response .= "allow desktop composition:i:0\r\n";
			    $response .= "disable full window drag:i:1\r\n";
			    $response .= "disable menu anims:i:1\r\n";
			    $response .= "disable themes:i:0\r\n";
			    $response .= "disable cursor setting:i:0\r\n";
			    $response .= "bitmapcachepersistenable:i:1\r\n";
			    $response .= "full address:s:$ip\r\n";
			    $response .= "audiomode:i:2\r\n";
			    $response .= "redirectprinters:i:1\r\n";
			    $response .= "redirectcomports:i:0\r\n";
			    $response .= "redirectsmartcards:i:1\r\n";
			    $response .= "redirectclipboard:i:1\r\n";
			    $response .= "redirectposdevices:i:0\r\n";
			    $response .= "redirectdirectx:i:1\r\n";
			    $response .= "autoreconnection enabled:i:1\r\n";
			    $response .= "authentication level:i:0\r\n";
			    $response .= "prompt for credentials:i:0\r\n";
			    $response .= "negotiate security layer:i:1\r\n";
			    $response .= "remoteapplicationmode:i:0\r\n";
			    $response .= "alternate shell:s:\r\n";
			    $response .= "shell working directory:s:\r\n";
			    $response .= "gatewayhostname:s:\r\n";
			    $response .= "gatewayusagemethod:i:4\r\n";
			    $response .= "gatewaycredentialssource:i:4\r\n";
			    $response .= "gatewayprofileusagemethod:i:0\r\n";
			    $response .= "promptcredentialonce:i:1\r\n";
			    $response .= "use redirection server name:i:0\r\n";
			    $response .= "drivestoredirect:s:\r\n";

			}

			$responseType='ascii';
		    }



	    }

	    ##########################################
	    ## Commands that Do Not Require Auth
	    ##########################################

	    if ($params->{'command'} =~ /getvpnsoftware/i)
	    {
		my $path = '/var/www/openvpn.exe';
		if (-f $path)
		{
		    &doSendFile('openvpn.exe',$path);
		}
	    }

	    if ($params->{'command'} =~ /getbpvpnsoftware/i)
	    {
		my $path = '/var/www/bpvpn.msi';
		if (-f $path)
		{
		    &doSendFile('bpvpn.msi',$path);
		}
	    }

	    if ($params->{'command'} =~ /getmacbpvpnsoftware/i)
	    {
		my $path = '/var/www/tunnelblick.dmg';
		if (-f $path)
		{
		    &doSendFile('tunnelblick.dmg',$path);
		}
	    }

	    if ($params->{'command'} =~ /^getkey$/i)
	    {

		my $_date = `date`;
		chomp($_date);

		my $_cleanUsername = $params->{'username'};

		$_cleanUsername =~ s/.*\\//g;
		$_cleanUsername =~ s/\@.*//g;

		my $_unencrypted = "";

		$_unencrypted .= "$CONFIG_USER_KEY_PASSWORD|";
		$_unencrypted .= "$params->{'first'}|";
		$_unencrypted .= "$params->{'last'}|";
		$_unencrypted .= "$_cleanUsername|";
		$_unencrypted .= "bp.local|";
		$_unencrypted .= $_date;

		$params->{'key'} = &encrypt($_unencrypted);
		$params->{'password'} = &encrypt($params->{'password'});

		if (&isValidUser())
		{
		    if ($responseType eq "file")
		    {
			$responseFile = "key.txt";
			$response = undef;
			$response = '';
			$response = $params->{'key'};
		    }
		    else
		    {
			$response->{'response'}->{'code'} = 200;
			$response->{'response'}->{'message'} = "User Is Valid";
			$response->{'response'}->{'key'} = $params->{'key'};
		    }
		}
		else
		{
		    $response->{'error'}->{'code'} = 500;
		    $response->{'error'}->{'message'} = "Authentication Failed";
		}

	    }

	    if ( $params->{'command'} =~ /getkeyarchive/i )
	    {

		my $_date = `date`;
		chomp($_date);

		my $_cleanUsername = $params->{'username'};

		$_cleanUsername =~ s/.*\\//g;
		$_cleanUsername =~ s/\@.*//g;

		my $_unencrypted = "";

		$_unencrypted .= "$CONFIG_USER_KEY_PASSWORD|";
		$_unencrypted .= "$params->{'first'}|";
		$_unencrypted .= "$params->{'last'}|";
		$_unencrypted .= "$_cleanUsername|";
		$_unencrypted .= "bp.local|";
		$_unencrypted .= $_date;

		$params->{'key'} = &encrypt($_unencrypted);
		$params->{'password'} = &encrypt($params->{'password'});

		if (&isValidUser())
		{

		    my $cmd = "";

		    &doGenerateCertificates( $authenticatedUser->[3] );

		    ## Add config files to the archive

		    ## Build the list
		    my @keyfiles = ();
		    my $path     = '/etc/openvpn/easy-rsa/keys/user-' . $authenticatedUser->[3] . '.crt';
		    push( @keyfiles, $path );
		    my $path = '/etc/openvpn/easy-rsa/keys/user-' . $authenticatedUser->[3] . '.key';
		    push( @keyfiles, $path );
		    my $path = '/etc/openvpn/easy-rsa/keys/ca.crt';
		    push( @keyfiles, $path );

		    ## Create the output directory
		    if ( -d "/tmp/$$.tblk" )
		    {
			$cmd = "rm -rf /tmp/$$.tblk";
			print STDERR "C: $cmd\n";
			system($cmd);
			if ( -d "/tmp/$$.tblk" )
			{
			    &error( 450, "Could not build archive" );
			}
		    }

		    if ( !-d "/tmp/$$.tblk" )
		    {
			$cmd = "mkdir /tmp/$$.tblk";
			print STDERR "C: $cmd\n";
			system($cmd);
		    }

		    ## Move the config files to the output directory
		    foreach my $keyfile (@keyfiles)
		    {
			if ($keyfile !~ /ca.crt/)
			{
			    $dst = $keyfile;
			    $dst =~ s/.*\./bp./;
			    $cmd = "cp $keyfile /tmp/$$.tblk/$dst";
			}
			else
			{
			    $cmd = "cp $keyfile /tmp/$$.tblk";
			}
			print STDERR "C: $cmd\n";
			system($cmd);
		    }

		    ## Build the openvpn configuration file
		    my $ovpnconfig = undef;

		    $ovpnconfig .= "client\r\n";
		    $ovpnconfig .= "dev tun\r\n";
		    $ovpnconfig .= "proto tcp\r\n";
		    $ovpnconfig .= "remote 66.210.189.134 995\r\n";
		    $ovpnconfig .= "resolv-retry infinite\r\n";
		    $ovpnconfig .= "nobind\r\n";
		    $ovpnconfig .= "persist-key\r\n";
		    $ovpnconfig .= "persist-tun\r\n";
		    $ovpnconfig .= "ca ca.crt\r\n";
		    $ovpnconfig .= "cert bp.crt\r\n";
		    $ovpnconfig .= "key bp.key\r\n";
		    $ovpnconfig .= "comp-lzo\r\n";

		    ## Write the file
		    open(OUT,">/tmp/$$.tblk/bp.ovpn");
		    print OUT $ovpnconfig;
		    close(OUT);

		    ## LAZY LAZY LAZY - This will create collisions - You should fix this loser

		    my $date = `date +%m-%d-%Y`;
		    chomp($date);

		    ## Make package have a friendly name
		    if (-d "/tmp/$date.tblk")
		    {
			$cmd = "rm -rf /tmp/$date.tblk";
			system($cmd);
		    }

		    $cmd = "mv /tmp/$$.tblk /tmp/$date.tblk";
		    system($cmd);

		    # Compress the filee
		    $cmd = "cd /tmp;zip -r $$.zip ./$date.tblk/";
		    system($cmd);

		    &doSendFile("$date.zip","/tmp/$$.zip");
		}

	    }


	}

    }

}

sub doGenerateCertificates()
{
    eval 
    {
	my $_username = shift;

	my $_cmd = "setup_vpn_user user-$_username > /dev/null";
	system($_cmd);
	return();
    }
}

sub shutDown()
{
    exit($_[0]);
}

sub doSendFile()
{

    my $name	        = shift;
    my $fullpath        = shift;

    my $buffer          = undef;
    my $bytesSent       = undef;
    my $fileSize        = undef;
    my $cnt             = undef;
    my $fileName        = undef;
    my $bufferSize	= 4096;
    my @elements        = ();

    my @stats           = stat($fullpath);
    $fileSize           = $stats[7];

    @elements           = split(/\//,$fullpath);
    $fileName           = $elements[$cnt-1];

    if (!-f $fullpath)
    {
        &error(500,"File not found [7784]: $fileName");
	return;
    }

    print "Content-Length: $fileSize\n";
    print "Content-Disposition: Attachment; filename=$name\n";
    print "Connection: close\n";
    print "Accept-Ranges: none\n";
    print "Content-type:  application/x-msdos-program\n\n";

    &debug('sending',"Sending $fullpath to $ENV{'REMOTE_ADDR'} as $name");

    open(IN,"< $fullpath");
    while (read(IN,$buffer,$bufferSize))
    {

        print $buffer;

        $bytesSent = $bytesSent + length($buffer);

	if ($fileSize - $bytesSent < $bufferSize)
	{
	    read(IN,$buffer,$fileSize - $bytesSent);
	    print $buffer;
	    last;
	}

    }
    close(IN);

    # Exit since we've already sent poo during this session we can't resend a response
    &shutDown(0);

}

sub isRDPPossible
{

    if ( -d $CONFIG_PATH_USER_LOGIN )
    {
	my @files = `ls $CONFIG_PATH_USER_LOGIN`;

	## Deal with case issues
	foreach my $file (@files)
	{
	    chomp($file);

	    ## Get the IP Address for their machine
	    if ($file =~ /$authenticatedUser->[3]/i)
	    {
		my $ip = undef;
		my $_path = $CONFIG_PATH_USER_LOGIN . '/' . $file;
		if ( -f $_path )
		{
		    open( IN, "< $_path" );
		    my $_machineName = <IN>;
		    close(IN);

		    $_machineName =~ s/(\n|\r)//g;

		    $ip = `host $_machineName`;
		    chomp($ip);

		    if ($ip =~ /has address/)
		    {
			$ip =~ s/.*has address //g;
		    }
		}

		if ($ip ne "")
		{
		    print STDERR "isRDP: $ip\n";
		    return $ip;
		}

		last;
	    }
	}
    }

    return undef;
}


sub isValidUser()
{

#    $params->{'key'} = $user;
#    $params->{'password'} = $pass;

    my $_key = undef;
    my $_password = undef;
    my $_user = undef;

    if (!$params->{'key'} || !$params->{'password'})
    {
	return undef;
    }
    else
    {
	$_key = $params->{'key'};

	my $_decryptedKey = &decrypt($_key);

	&debug('decryptedKey',$_decryptedKey);

	$_user = &getKeyParts($_decryptedKey);

	&debug('user',$_user);
	
	$_password = $params->{'password'};
	$_password = &decrypt($_password);

	&debug('password',$_password);

	if ($_user->[0] ne $CONFIG_USER_KEY_PASSWORD)
	{
	    return undef;
	}

	$authenticatedUser = $_user;
	
    }
    if (!($ldap = Net::LDAP->new($CONFIG_DOMAIN_CONTROLLER))) 
    { 
	&error(500,"Couldn't Connect to Domain Controller");
    }

    if ($_user->[3] =~ /rebecc/i)
    {
	return undef;
    }

    my $testResponse = $ldap->bind( 
				    $_user->[3] . '@' . $_user->[4],
				    password=>$_password
				  );

    if (!$testResponse->code())
    {
	return 1;
    }

    return undef;
}

sub debug()
{
    if ($params->{'debug'} eq "fluffy")
    {
	$response->{'debug'}->{$_[0]} = $_[1];
    }
}

sub getKeyParts()
{
    my $_string = shift;
    my @vals = split(/\|/,$_string);
    return \@vals;
}

sub doInitialize()
{
    $response->{'settings'}->{'vpnclientversion'} = $CONFIG_VPN_CLIENT_VERSION;
}

sub getParams()
{
    my @_parms = $c->param();

    foreach my $_parm (@_parms)
    {
	$params->{$_parm} = $c->param($_parm);
    }

    if ($params->{'responsetype'})
    {
	$responseType = $params->{'responsetype'};
    }
}

sub error()
{
    $response->{'error'}->{'code'} = $_[0];
    $response->{'error'}->{'message'} = $_[1];
}

sub decrypt()
{
    my $_encrypted = shift;

    my $_decoded = decode_base64($_encrypted);

    ## Grab the PBKDF2 salt (to mimic C#)
    my ($k, $t, $u, $ui, $i);
    $t = "";
    for ($k = 1; length($t) <  $CONFIG_CYPHER_KEYLEN; $k++) {
	$u = $ui = &hmac_sha1($CONFIG_CYPHER_SALT.pack('N', $k), $CONFIG_CYPHER_PASSWORD);
	for ($i = 1; $i < $CONFIG_CYPHER_ITER; $i++) {
	    $ui = &hmac_sha1($ui, $CONFIG_CYPHER_PASSWORD);
	    $u ^= $ui;
	}
	$t .= $u;
    }

    my $cipherKey =  substr($t, 0, $CONFIG_CYPHER_KEYLEN);

    my $cypher =  Crypt::CBC->new(
	{
	    'key'		=> $cipherKey,
	    'cipher'		=> 'Rijndael',
	    'iv'		=> $CONFIG_CYPHER_INITIAL_VECTOR,
	    'literal_key'	=> 1,
	    'header'		=> 'none',
	    'padding'		=> 'standard',
	    'keysize'		=> $CONFIG_CYPHER_KEYLEN
	});

    return $cypher->decrypt($_decoded);

}

sub encrypt()
{

    my $_plaintext = shift;

    ## Grab the PBKDF2 salt (to mimic C#)
    my ($k, $t, $u, $ui, $i);
    $t = "";
    for ($k = 1; length($t) <  $CONFIG_CYPHER_KEYLEN; $k++) {
	$u = $ui = &hmac_sha1($CONFIG_CYPHER_SALT.pack('N', $k), $CONFIG_CYPHER_PASSWORD);
	for ($i = 1; $i < $CONFIG_CYPHER_ITER; $i++) {
	    $ui = &hmac_sha1($ui, $CONFIG_CYPHER_PASSWORD);
	    $u ^= $ui;
	}
	$t .= $u;
    }

    my $cipherKey =  substr($t, 0, $CONFIG_CYPHER_KEYLEN);

    my $cypher =  Crypt::CBC->new(
	{
	    'key'		=> $cipherKey,
	    'cipher'		=> 'Rijndael',
	    'iv'		=> $CONFIG_CYPHER_INITIAL_VECTOR,
	    'literal_key'	=> 1,
	    'header'		=> 'none',
	    'padding'		=> 'standard',
	    'keysize'		=> $CONFIG_CYPHER_KEYLEN
	});

    my $_encrypted = $cypher->encrypt($_plaintext);
    my $_encoded = encode_base64($_encrypted);
    $_encoded =~ s/[\h\v]+//g;

    return $_encoded;

}

sub doOutputResponse()
{
    if ($responseType eq "xml")
    {
	print "Content-Type:  text/xml\n\n";
	print $xml->XMLout($response,NoAttr=>1,RootName=>'vpn_api_response',XMLDecl=>1);
    }

    if ($responseType eq "json")
    {
	print "Content-Type:  application/json\n\n";
	print encode_json($response);
    }

    if ($responseType eq 'ascii')
    {
	print "Content-Type:  text/ascii\n\n";
	print $response;
    }

    if ($responseType eq 'file')
    {
	open(OUT,">/tmp/$$.file");
	print OUT $response;
	close(OUT);
	&doSendFile($responseFile,"/tmp/$$.file");
	unlink("/tmp/$$.file");
    }
}

&main();
&doOutputResponse();
exit(0);
