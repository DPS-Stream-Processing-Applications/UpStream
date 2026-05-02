To evaluate the scaler we need to set up the Kafka event generator implemented in `./beam-applications-java/kafkaProducer/` on the ssh jump host of the cluster.

This is required because kafka will only serve the ipaddresses of the pods which are not available from outside the Chameleon Cloud network.

## Dataset Prep
Make sure you created you required dataset using the [senMLScenarioBuilder](./senMLScenarioBuilder/)

## Sync to Jump Host
You can run the `uploat_to_bastion` utility which will upload all relevant files to the bastion.

## Nix
You will have to install nix on the bastion following the [README section](./README.md#installing-nix).

## Forwarding

In order for portforwaring of kubectl to work make sure you manually ssh to all the instances before proceeding

```bash
ssh k3s-server
ssh k3s-agent-1
ssh k3s-agent-2
```
Now you can run the forwarding utilities

```bash
forward_kubectl
forward_kafka
```

```bash
java -jar $PROJECT_ROOT/KafkaProducer.jar $PROJECT_ROOT/data/riot_events_TAXI_constant_rate_scenario.csv $(nproc) "senml-source"
```
