# Setup
To set up the Kubernetes cluster this project makes use of k3s.
The `k3s-ansible` project is used to set up a k3s cluster using Ansible.

```bash
ansible-playbook k3s-ansible/playbooks/site.yml \
    --extra-vars kubeconfig="$PROJECT_ROOT/.kube/config"
ansible-playbook k3s-ansible/playbooks/reset.yml
```

