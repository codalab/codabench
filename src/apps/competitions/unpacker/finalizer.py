from pprint import pprint
from uuid import UUID

from rest_framework.exceptions import ValidationError
from api.serializers.competitions import CompetitionSerializer
from api.serializers.tasks import TaskSerializer, SolutionSerializer
from competitions.unpacker.utils import get_data_key


class Finalizer:

    def __init__(self, data, creator):
        self.data = data
        self.creator = creator

    def finalize(self):
        # Local import so we don't hit issues
        from competitions.unpacker.exceptions import CompetitionUnpackingException

        self._create_tasks()
        self._create_solutions()

        print("MY god damn data is {}".format(self.data['competition']))

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
            # print("My god damn index: {}".format())
            for phase_data in self.data['competition']['phases']:
                for index, temp_task_data in enumerate(phase_data['tasks']):
                    print("*****************************************")
                    print(temp_task_data)
                    print(isinstance(temp_task_data, UUID))
                    print("*****************************************")
                    if not isinstance(temp_task_data, UUID):
                        if temp_task_data['index'] == temp_index:
                            phase_data['tasks'][index] = new_task.key
                            print("*****************************************")
                            print(temp_task_data)
                            print("*****************************************")
            # self.data['competition']["tasks"][temp_index] = new_task.key

    def _create_solutions(self):
        for solution_data in self.data['solutions']:
            serializer = SolutionSerializer(data=solution_data)
            serializer.is_valid(raise_exception=True)
            new_solution = serializer.save()
            self.data['competition']['solutions'][solution_data['index']] = new_solution.key