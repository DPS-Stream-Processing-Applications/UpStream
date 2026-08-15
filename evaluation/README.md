To evaluate the scaler we need to set up the Kafka event generator implemented in `./beam-applications-java/kafkaProducer/` on the ssh jump host of the cluster.

This is required because kafka will only serve the ipaddresses of the pods which are not available from outside the Chameleon Cloud network.

## Dataset Prep
Make sure you created you required dataset using the [senMLScenarioBuilder](./senMLScenarioBuilder/)

## Event generator setup
To upload the eventgenerator to the bastion and generate events for the pipeline starting there:

```bash
set_up_bastion
ssh jump
cd event_generator
nix develop
```
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

### Stop forwarding:
It might be the case that the forwarding precess gets stuck in the background you can run the following command to kill them:

```bash
lsof -ti :6443 | xargs kill
lsof -ti :9093 | xargs kill
```


```bash
java -jar $PROJECT_ROOT/KafkaProducer.jar $PROJECT_ROOT/data/riot_events_TAXI_constant_rate_scenario.csv $(nproc) "senml-source"
java -jar $PROJECT_ROOT/KafkaProducer.jar $PROJECT_ROOT/data/riot_events_TAXI_constant_rate_scenario.csv $(nproc) "senml-cleaned"
```

## Downloading benchmark data

```bash
uv run python main.py 2026-08-14T16:56:31 2026-08-14T17:16:51 ./values.parquet
```



# Baseline without Scaling

We compare a baseline  of ETL since it is the most linear DAG, with the maximum size of taskmanager (small) with 64 replicas
and (taskmanager-large) with 8 replicas to show the overhead of networking / the gains of joining taskmanagers to bigger instances.

For 64 replicas we can see that running the event generator with 10000 events per minute bottlenecks (backpressures) at only ~ 900 events per second.

Start of run at 2026-08-14 16:57:30

large with 8 replicas start at 

Start of run at 2026-08-07 19:17:30 Bottlenecking at ~ 10500 events per second

Establish 9000 Events per second as the upper limit for all future experiments.


# Static Load

HPA setup:
Start reduce replicas of `flink-application-cluster-taskmanager` deployment from the 64 to 2
static load TAXI generated with 9000 events/s

Start of run with HPA and ETL at 2026-08-07 21:07:30
