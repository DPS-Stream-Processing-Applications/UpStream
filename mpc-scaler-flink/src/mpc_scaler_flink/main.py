from typing import List

import numpy as np
from kubernetes import client, config

from mpc_scaler_flink.mpc_controller import MPCController

from .pod import Pod, PodCapacity
from .pod_allocator import PodAllocator


def scale_deployment(deployment_name, namespace, replicas):
    config.load_kube_config()

    apps_v1 = client.AppsV1Api()

    scale = {"spec": {"replicas": replicas}}

    try:
        response = apps_v1.patch_namespaced_deployment_scale(
            name=deployment_name, namespace=namespace, body=scale
        )
        print(f"Deployment {deployment_name} scaled to {replicas} replicas.")
        return response
    except client.ApiException as e:
        print(f"Error scaling deployment: {e}")


def main():

    # deployment_name = "flink-session-cluster-taskmanager"
    # namespace = "default"
    # replicas = 3
    # scale_deployment(deployment_name, namespace, replicas)

    ### TODO: CONNECT TO PROMETHEUS INSTANCE ###

    controller = MPCController()
    # TODO: read from Prometheus
    controller.initial_measurement(np.array([0, 0, 0]))
    allocator: PodAllocator = PodAllocator(utilisation_factor=0.8)

    ### TODO: LOAD REPLICA CONFIGS ###
    pods: List[Pod] = [Pod(capacity, 1) for capacity in PodCapacity]
    print(pods)

    i = 0
    while i < 6:
        print("infinite")
        # TODO: read metrics from Prometheus
        scaling_factor = controller.measurement_step(np.array([0, 0, 0]))

        current_task_slot_count: int = sum(
            [pod.replica_count * pod.task_slot_capacity.value for pod in pods]
        )
        print(f"current_task_slot_count: {current_task_slot_count}")

        new_task_slot_count: int = round(current_task_slot_count * scaling_factor)
        print(f"new_task_slot_count: {new_task_slot_count}")

        updated_pods: List[Pod] = allocator.allocate_pods(new_task_slot_count, pods)
        print(updated_pods)
        i += 1
        ### TODO: update pod deployments in Kubernetes ###
