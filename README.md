# Generic Credential Provider for accessing Private Container Registries from Kubernetes

This is currently designed to answer a simple question - how can I authenticate to my private
container registry from Kubernetes (or, more accurately, the kubelet daemon).

I was inspired by the
[ECR Credential Provider](https://cloud-provider-aws.sigs.k8s.io/credential_provider/)
and so wrote my own, following the details in the
[Kubelet Credential Provider API Documentation](https://kubernetes.io/docs/tasks/administer-cluster/kubelet-credential-provider/).

_Skip to [Setting up the Credential Provider](#setting-up-the-credential-provider)_ | _Skip to [Issues, Feature Requests, Changes and Security Concerns](#issues-feature-requests-changes-and-security-concerns)_

## Setting up the Credential Provider

The credential Provider requires several steps on your worker nodes to configure it for use.

In my examples below, I'll use the following paths;

* `/etc/sysconfig/kubelet` - The file which contains the "KUBELET_EXTRA_ARGS" settings for the
systemd unit file. Your systemd unit file may be configured differently.
* `/usr/local/bin/image-credential-provider` - The location where the credential provider is
stored.
* `/etc/kubernetes/image-credential-provider-config.json` - The file which configures how to invoke
the credential providers.
* `/etc/kubernetes/registry` - The directory which contains the static credentials for pulling
images from the registries. While this can be defined to another path, this has not been tested
in live service, outside the automated test tooling, and particularly not in the context of the
credential provider configuration file.

I have used an example domain name to specify the registry provider; `registry.example.org`

### Configuring Kubelet

Configure the Kubelet service on your worker node. On my system the kubelet service is configured
to start as a systemd unit that loads settings from `/etc/sysconfig/kubelet`. Your system may use
another file, perhaps `/etc/defaults/kubelet`. Check the systemd unit file for any linked file
which contains a series of options (such as `--node-labels`, `--node-ip` or `--hostname-override`).

If you don't have one, you can edit the systemd unit for kubelet instead to add the settings.

In this file, add the following extra arguments:

* `--image-credential-provider-bin-dir /usr/local/bin/image-credential-provider`
* `--image-credential-provider-config /etc/kubernetes/image-credential-provider-config.json`

Note that these paths are arbitrary and can be changed to somewhere more in-line with your own
environment.

### Deploying the credential provider script

The key file to obtain is [generic-credential-provider](generic-credential-provider) which should
be placed into the directory specified in `--image-credential-provider-bin-dir`, and configured as
an executable file. Currently, all of the invoked libraries are configured as part of the standard
Python3 libraries, so no extra python packages should be required.

### Configure which registries need the credential provider to execute

Edit the file specified in `--image-credential-provider-config` to incorporate the following:

```json
{
  "apiVersion": "kubelet.config.k8s.io/v1",
  "kind": "CredentialProviderConfig",
  "providers": [
    {
      "name": "generic-credential-provider",
      "matchImages": [
        "registry.example.org"
      ],
      "defaultCacheDuration": "5m",
      "apiVersion": "credentialprovider.kubelet.k8s.io/v1"
    }
  ]
}

```

Change the `matchImages` list according to your requirements.

### Configure the credentials file

Using the path `/etc/kubernetes/registry` create files that match all or part of the hostname for
the registry. In this case, you can define a file called `registry.example.org.json`, or
`example.org.json` or even `org.json`. This file needs to contain the credentials that are needed
to authenticate to that registry, using the following format:

```json
{
    "username": "SOME_USERNAME",
    "password": "SOME_PASSWORD_OR_TOKEN",
    "duration": "0h5m0s"
}
```

Note that the duration field is optional and will default to `0h5m0s`. The other values, if left
blank or omitted, it will return an empty string for the username or password.

### Testing your installation

There are three tests we can do here;

1. `echo '{"apiVersion":"credentialprovider.kubelet.k8s.io/v1","kind":"CredentialProviderRequest","image":"registry.example.org/org/image:latest"}' | generic-credential-provider` should
return the authentication value.
2. `echo '{"apiVersion":"credentialprovider.kubelet.k8s.io/v1","kind":"CredentialProviderRequest","image":"not-here.tld/test:latest"} | generic-credential-provider` should return an
error message.
3. Provision a pod using the expected registry path, and check your syslog for a message from the
`generic-credential-provider` with the string `Credential request fulfilled for {DNSNAME}` or `Failed to
fulfill credential request for {DNSNAME}`.

## Issues, Feature Requests, Changes and Security Concerns

If you have found an issue with this script or want a feature to be added, please use the
[issues tab above](https://github.com/JonTheNiceGuy/generic-credential-provider/issues),
however, if you've found a security concern, please contact
[jon@sprig.gs](mailto:jon@sprig.gs?subject=generic-credential-provider%20Security%20Issue)
directly.

If you're looking to get involved in the project, and don't know what is of interest, please take a
look at the issues tagged
[Feature Request](https://github.com/JonTheNiceGuy/generic-credential-provider/issues?q=is%3Aissue+is%3Aopen+label%3A%22Feature+Request%22).
If you've got an idea on something you want to add, please
[raise an issue](https://github.com/JonTheNiceGuy/generic-credential-provider/issues) first, just
to make sure it's in line with what the project wants. Oh, and if you spot a typo or small error,
I'm happy to receive "drive-by" pull requests on those! :grin:
