# Setting up GRID proxy for data access

CMS data is distributed across the Worldwide LHC Computing Grid (WLCG), a global network of computing centers. Accessing this data requires proper authenticaiton through a GRID certificate and proxy.

A GRID certificate is a digital credential that identifies you to the GRID. If you don’t have a GRID certificate, follow the instructions [here](https://twiki.cern.ch/twiki/bin/view/CMSPublic/WorkBookStartingGrid#ObtainingCert). You need to generate the certificate and export it to the `~/.globus` directory in your LXPLUS user space, which is the standard location.

The GRID certificate alone cannot be used directly for data access. You must generate a VOMS (Virtual Organization Membership Service) proxy. The proxy is a short-lived credential derived from your certificate, which includes yout CMS Virtual Organization (VO) membership information and has a limited lifetime for security.

Execute the following command to generate a CMS specific proxy:

```bash
voms-proxy-init --voms cms --valid 192:00 --out $HOME/.globus/x509up_u$(id -u)
```

This command generates the proxy to be used with CMS data and sets its lifitime to 192 hours, if you do not specify this, it defaults to 12 hours, and 192 hours is the maximum allowed.

We store the proxy inside our home directory. If you do not specify the output, it is stored by default in the `/tmp/` directory. The `x509up_u$(id -u)` format is a naming convention that includes your user ID.

!!! warning "Important"
    When the proxy expires, you must regenerate it using the same command. If not, it will result in authentication failures.

Verify that the certificate was correctly generated. First, we need to tell the system where our proxy is located, as mentioned earlier, the default directory is `/tmp/`, and the system will not find it if we saved it elsewhere. Therefore, we export the actual location:

```bash
export X509_USER_PROXY=$HOME/.globus/x509up_u$(id -u)
```

This environment variable tells the data access tools where to find your autentication credentials. Add this line to your `~/.bashrc` file to make it permanent. The next command shows us if it is correctly configured and vaild:

```bash
voms-proxy-info --all
```

Check that the timeleft value shows sufficient remaining time before expiration.
