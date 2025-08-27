from enum import Enum


class PodCapacity(Enum):
    SMALL = 4
    MEDIUM = 8
    LARGE = 16


class Pod:
    def __init__(self, task_slot_capacity: PodCapacity, replica_count: int):
        if replica_count < 0:
            raise ValueError(
                f"Expected a positive integer for `replica count`, got {replica_count}"
            )
        self.task_slot_capacity = task_slot_capacity
        self.replica_count = replica_count

    def __repr__(self):
        return f"Pod(capacity={self.task_slot_capacity.name}, replica_count={self.replica_count})"
