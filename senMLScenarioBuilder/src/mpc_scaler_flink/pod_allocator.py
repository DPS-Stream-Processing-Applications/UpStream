from typing import List

from .pod import Pod


class PodAllocator:
    def __init__(self, utilisation_factor: float = 1.0):
        self.utilisation_factor = utilisation_factor

    def allocate_pods(self, number_of_slots: int, pods: List[Pod]) -> List[Pod]:
        allocated_pods: List[Pod] = []
        sorted_pods: List[Pod] = sorted(
            pods, key=lambda p: p.task_slot_capacity.value, reverse=True
        )

        for pod in sorted_pods:
            pod.replica_count = 0

            while number_of_slots >= round(
                pod.task_slot_capacity.value * self.utilisation_factor
            ):
                number_of_slots -= pod.task_slot_capacity.value
                pod.replica_count += 1

            allocated_pods.append(pod)

        # NOTE: The number of slots may be below the smallest pod capacity.
        # If this is the case, the replica count must be increased by 1.
        # 0 < number_of_slots < smallest_pod_capacity
        if number_of_slots > 0:
            allocated_pods[-1].replica_count += 1

        return allocated_pods
