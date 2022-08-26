class AssignmentManager:

    def __init__(self, min_walk_in_pool, walk_in_pool):
        self.min_walk_in_pool = min_walk_in_pool
        self.walk_in_pool = walk_in_pool



class VehicleScannedTrigger():

    def __init__(self, min_walk_in_pool, walk_in_pool):
        self.min_walk_in_pool = min_walk_in_pool
        self.walk_in_pool = walk_in_pool

    def walk_in_pool_less_than_minimum_pool(self):
        return len(self.walk_in_pool) < self.min_walk_in_pool

    def vehicle_can_meet_deadline_with_l2_at_max_rate_with_slack(self):
        pass

    def assign_vehicle_to_walk_in_poll(self):
        if self.walk_in_pool_less_than_minimum_pool():
            self.prefer_dcfc()
        else:
            self.prefer_l2()

    def assign_vehicle_to_earlist_reservation(self):
        if self.vehicle_can_meet_deadline_with_l2_at_max_rate_with_slack():
            self.prefer_l2()
        else:
            self.prefer_dcfc()

    def unassigned_reservation_exists(self):
        pass

    def get_vehicle_scanned_assignment(self):

        if self.unassigned_reservation_exists()
            self.assign_vehicle_to_earlist_reservation()
        else:
            self.assign_vehicle_to_walk_in_poll()
