
from domain.ports.activity_repository import ActivityRepository
from domain.ports.antenna_repository import AntennaRepository

class AutoAssignOrchestrator:
    def __init__(
        self,
        activity_repository: ActivityRepository,
    ):
        self.pass_activity_repository = activity_repository

    
    def assign_antennas_to_activities(self, activities: List[PassActivity]) -> List[AntennaAssignment]:
        # 1. Obtener todas las antenas activas desde el repositorio
        active_antennas = self.antenna_repo.get_all_active_antennas()

        successful_assignments = []

        for activity in activities:
            # 2. Obtener antenas disponibles para ese rango de tiempo
            available_antennas = find_available_antennas(
                activity=activity,
                antennas=active_antennas,
                assignment_repo=self.assignment_repo
            )

            if available_antennas:
                # 3. Elegir la mejor antena disponible (por ahora, la primera)
                selected_antenna = available_antennas[0]

                # 4. Crear y guardar la asignación
                assignment = assign_antenna_to_activity(activity, selected_antenna)
                self.assignment_repo.save_assignment(assignment)

                successful_assignments.append(assignment)

        return successful_assignments

