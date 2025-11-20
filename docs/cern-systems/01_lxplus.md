# LXPLUS

LXPLUS (Linux Public Login User Service) is the primary access point to the CERN computing cluster. This service shaped the login nodes used to interact with our files, directories, environment, and computational environment. from these login nodes, you submit the script to executed in the worker nodes where the actual processing occurs.

As the name suggests, LXPLUS operates on Linux-based system, in particular a Red Hat Enterprise Linux distribution. To establish a conneciton to LXPLULS, you need:

* A valid CERN user account
* SSH (Secure shell) client software

There are multiple SSH client options; for example, PuTTY, Bitvise, or the terminal either on either windows, mac, or linux. All methods require your CERN username and authentication credentials. More information in [The LXPLUS Service](https://lxplusdoc.web.cern.ch/). 

Upon connecting, You will be asked for your password and verification code. If you have not yet activated the two factor authentication (2FA) look up [Setting up 2FA using your Smartphone](https://cern.service-now.com/service-portal?id=kb_article&n=KB0006587). 

## Logging into LXPLUS

Establish a secure shell connection to the LXPLUS cluster using your CERN credentials. Exmaple using CLI (command li\
ne interface):

```bash
ssh username@lxplus.cern.ch
```

Upon successful connection, you will be placed in your home directory.

![LXPLUS log in](assets/images/fig02-lxplus-login.png)

