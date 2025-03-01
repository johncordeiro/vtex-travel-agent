import requests
from weni import Skill
from weni.context import Context
from weni.responses import TextResponse

class AddressSkill(Skill):

    def execute(self, context: Context) -> TextResponse:
        cep = context.parameters.get("cep")
        return TextResponse(data=self.get_address(cep))

    def get_address(self, cep):
        base_url = f"https://viacep.com.br/ws/{cep}/json/"
        response = requests.get(base_url)

        return response.json()