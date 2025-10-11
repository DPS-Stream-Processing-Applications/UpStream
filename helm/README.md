# Setup
Follow all these commands in exactly this order to guarantee a smooth setup.

```bash
helm install \
cert-manager oci://quay.io/jetstack/charts/cert-manager \
--version v1.15.0 \
--namespace cert-manager \
--create-namespace \
--set crds.enabled=true
```

A part of the `riotbenchsinglejob` aplication requires the -


