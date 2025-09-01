To set up the Kubernetes cluster this project makes use of k3s.
The `k3s-ansible` project is used to set up a k3s cluster using Ansible.

# Prerequisites
> [!WARNING]
> Luckily Ansible makes use of `ssh` under the hood. This means we can reuse this
> projects [ssh config](../.ssh/config). Make sure it is set up properly before you proceed.

The agent nodes of the cluster need to know how to reach their server node.
This is achieved through the `api_endpoint` field in [inventory.yml](inventory.yml)
Make sure it matches the IP of `k3s-server` before you try to execute this playbook.

# Setup
The following two commands allow for the creation and destruction of the k3s cluster.
```bash
ansible-playbook k3s-ansible/playbooks/site.yml \
    --extra-vars kubeconfig="$PROJECT_ROOT/.kube/config"

ansible-playbook k3s-ansible/playbooks/reset.yml
```
# Aftermath
The playbook will copy the kubectl config of the cluster to `.kube/config`.
This allows you to [connect to the remote cluster locally](../README.md#forwarding-kubectl).

