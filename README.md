haze-alert
==========

Sends an SMS to your mobile phone when official 3-hour PSI readings cross a threshold.

Continuously reports the official PSI reading as it is updated, until the reading falls below the threshold.

##Usage
	$ ./haze-alert.py --help
	usage: haze-alert.py [-h] [-v] [-t] [-u] [-i IDENTITY]
	                     scratch datasource threshold
	
	positional arguments:
	  scratch               haze-alert scratch file
	  datasource            the file from which PSI data should be loaded. Specify
	                        --url if the datasource is a URL
	  threshold             the PSI threshold above with an alert should be sent
	
	optional arguments:
	  -h, --help            show this help message and exit
	  -v, --verbose         turns on console output
	  -t, --test            test mode. Prints API call but does not send SMS.
	                        Always prints regardless of --verbose
	  -u, --url             specify to treat the datasource as a URL
	  -i IDENTITY, --identity IDENTITY
	                        Hoiio API identity file to use. Default: ~/.hoiioapi
	                        
##Installation
You will need a [Hoiio Developer Account](http://developer.hoiio.com/) to use this script.

Sending SMSes costs *money* (which can be quite rare), and my web infrastructure cannot handle the load of a public service. Hosting your own is the most scalable solution at the moment.

1. Sign up for one.
2. Create an App ID and Access Token.
3. Create the idenitity file on your local machine. If you only have the trial SGD10.00 credit that each user gets upon sign up, then you can only send SMSes to your own phone number.  
4. Set this script to run at a set interval. (You can use the API at [http://psi.qxcg.net/](http://psi.qxcg.net/) if you don't host your own.)

###Related Utilities
Check out the scraper and historian at [https://github.com/cgcai/psipy](https://github.com/cgcai/psipy).

##API File
The API file is a plain text document containing a single JSON object. The object contains one or more application names as keys. Each key has a JSON sub-structure containing that application's configuration parameters. The file may not contain comments.

The following is a sample `.hoiioapi`:

	{
		"hazealert": {
			"appid": "<some value>",
			"token": "<some value>",
			"number": "<some value>"
		}
	}

##Furture Work
1. Silent hours.
2. `--kiasu` flag for people who love reading about the weather every hour.