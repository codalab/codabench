from uuid import UUID

from api.serializers.competitions import CompetitionSerializer
from api.serializers.tasks import TaskSerializer, SolutionSerializer
from competitions.unpacker.utils import get_data_key


class Finalizer:

    def __init__(self, data, creator):
        self.data = data
        self.creator = creator

    def finalize(self):
        self._create_tasks()
        self._create_solutions()

        serializer = CompetitionSerializer(
            data=self.data['competition'],
            # We have to pass the creator here this special way, because this is how the API
            # takes the request.user
            context={"created_by": self.creator}
        )
        # try:
        serializer.is_valid(raise_exception=True)
        competition = serializer.save()
        return competition
        # except ValidationError as e:
        #     # TODO Convert this error to something nice? Output's something like this currently:
        #     # "{'pages': [{'content': [ErrorDetail(string='This field may not be blank.', code='blank')]}]}"
        #     raise CompetitionUnpackingException(str(e))

    def _create_tasks(self):
        for task_data in self.data['tasks']:
            temp_index = task_data['index']
            for file_type in ['ingestion_program', 'input_data', 'scoring_program', 'reference_data']:
                key = get_data_key(**task_data[file_type])
                task_data[file_type] = key
            serializer = TaskSerializer(
                data=task_data,
            )
            serializer.is_valid(raise_exception=True)
            new_task = serializer.save()
            for phase_data in self.data['competition']['phases']:
                for index, temp_task_data in enumerate(phase_data['tasks']):
                    if not isinstance(temp_task_data, UUID):
                        if temp_task_data['index'] == temp_index:
                            phase_data['tasks'][index] = new_task.key
            for solution_data in self.data['solutions']:
                for index, temp_task_data in enumerate(solution_data.get('tasks')):
                    if not isinstance(temp_task_data, UUID):
                        if temp_task_data['index'] == temp_index:
                            solution_data['tasks'][index] = new_task.key

    def _create_solutions(self):
        for solution_data in self.data['solutions']:
            temp_index = solution_data['index']
            serializer = SolutionSerializer(data=solution_data)
            serializer.is_valid(raise_exception=True)
            new_solution = serializer.save()
            for phase_data in self.data['competition']['phases']:
                for index, temp_solution_data in enumerate(phase_data.get('solutions', [])):
                    if not isinstance(temp_solution_data, UUID):
                        if temp_solution_data['index'] == temp_index:
                            phase_data['solutions'][index] = new_solution.key
