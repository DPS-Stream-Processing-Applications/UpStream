<div align="center">
<!-- INFO: The empty line is required for center to work.-->

[![Nix](https://img.shields.io/badge/Nix_devShell-%235277C3?style=for-the-badge&logo=NixOS&logoColor=white)](https://nixos.wiki/wiki/Flakes)
[![Helm](https://img.shields.io/badge/Helm-0F1689?style=for-the-badge&logo=Helm&logoColor=white)](https://helm.sh/)
[![Apache Flink](https://img.shields.io/badge/Apache%20Flink%201.18.1-E6526F?style=for-the-badge&logo=Apache%20Flink&logoColor=white)](https://flink.apache.org/)
[![Chameleon Cloud](https://img.shields.io/badge/Chameleon%20Cloud-042F55D?style=for-the-badge&logoColor=white)](https://www.chameleoncloud.org/)

</div>

# Description
This Projects contains all parts of the UpStream scaling framework. It makes use of domain specific metrics from the Flink application cluster to make a scaling decision using
[MPC](https://en.wikipedia.org/wiki/Model_predictive_control).
# Setup

> [!TIP]
> This repo makes use of [git submodules](https://git-scm.com/book/en/v2/Git-Tools-Submodules).
> To clone with all included submodules at once you can run:
> ``` bash
> git clone --recurse-submodules git@github.com:eprader/BSc_streamprocessing.git
> ```

This project contains a `flake.nix` file to manage all the dependencies that would usually need to be installed through a regular package manager
with the Nix package manager instead. The Nix Shell will provide an installation of Flink as well as the OpenJDK needed for the Gradle wrapper to work.

## Installing Nix
To install Nix follow the [official instructions](https://nixos.org/download) for your platform.
Following this, you need to enable `flakes` and `nix-command` for the Nix package manager that you just installed.
The "Other Distros, without Home-Manager" section of the [Flake Wiki](https://nixos.wiki/wiki/Flakes) will explain how to do this.
> [!TIP]
> If the `~/.config/nix` folder and `nix.conf` file do not already exist after installing, you need to create them manually.

## Nix Develop
After successfully installing Nix and enabling Flakes, you will be able to use the `nix develop` command in the root of the project to enter a
development shell managed by Nix. To exit the dev shell, use the `exit` command or hit `Ctrl+d`.

## Direnv
> [!NOTE]
> This step is entirely optional but may improve your development experience.

Using [Direnv](https://direnv.net/) will allow you to automatically launch the Nix `devShell` whenever you change into the project directory.
Direnv can also be detected by your IDE if a plugin exists.
You might also want to install [nix-direnv](https://github.com/nix-community/nix-direnv) to improve the Direnv experience with Nix.

## Kubernetes
For all the applications in this repository external resources are required.
These resources are all managed within a Kubernetes cluster.

### Local K8S Cluster
> [!IMPORTANT]
> Make sure you have [docker](https://www.docker.com/) installed on your system before reading further.

The nix dev shell provides `k3d` as means to spin up a local Kubernetes cluster.
Use the `k3d-cluster-config.yaml` file of this project to set up a preconfigured `test-cluster`.
See the following [guide on how to use a config file](https://k3d.io/v5.0.0/usage/configfile/#usage).
Follow the [quick start guide](https://k3d.io/v5.6.3/#quick-start) to set up an empty cluster.

### Connecting To a Remote Cluster
To make it as easy as possible to deploy the applications on a remote cluster follow the following steps:

### Kube Config of Remote Host
Kubectl needs a config file to know where the cluster is located an which credentials to use to connect to it. It's easiest to just copy the existing `config` file from the remote server node.
Using a Jump Host the following scp command will work:
```bash
scp -o "ProxyJump <proxy_user>@<proxy_ip>" <host_user>@<host_ip>:~/.kube/config ./.kube/config
```

#### SSH Tunnel
`kubectl` uses port 6443 to communicate with a cluster. You can forward this port on the remote host through the Jump Host.

```bash
ssh -J <proxy_user>@<proxy_ip> -L 6443:<host_ip>:6443 <host_user>@<host_ip> -N &
```

### Helm Deployment
All the applications of this repository depend on external resources like an Apache `Kafka` cluster as well as a `mongoDB` database.
All dependencies for the applications are managed and deployed via a custom `helm chart` in the `helm-charts` directory.
Refer to the [README](./helm-charts/riot-applications/README.md) for an installation walkthrough.
