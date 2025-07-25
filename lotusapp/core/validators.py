import os
import magic
from django.core.exceptions import ValidationError

def validate_file_type(file):
    """
    Valida o tipo de arquivo usando a assinatura binária (magic numbers)
    para garantir que o tipo de conteúdo não foi falsificado.
    """
    # [cite_start]De acordo com o plano, apenas PDF é permitido [cite: 13, 151, 152]
    allowed_types = {
        'application/pdf': ['.pdf']
    }

    # [cite_start]Detecta o tipo real do arquivo lendo os primeiros 2048 bytes [cite: 261, 270]
    file_type = magic.from_buffer(file.read(2048), mime=True)
    file.seek(0)  # Retorna o ponteiro do arquivo para o início para leituras futuras

    # [cite_start]Verifica se o tipo detectado está na lista de permissões [cite: 272]
    if file_type not in allowed_types:
        raise ValidationError(f'Tipo de arquivo não permitido: {file_type}')

    # Opcional, mas recomendado: verificar se a extensão corresponde ao tipo real
    file_extension = os.path.splitext(file.name)[1].lower()
    if file_extension not in allowed_types.get(file_type, []):
        raise ValidationError(f'A extensão do arquivo "{file_extension}" não corresponde ao tipo de conteúdo real "{file_type}".')

    return True