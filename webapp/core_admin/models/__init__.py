from core_admin.models.dimensoes import (  # noqa: F401
    FonteRecurso,
    GrauNovidade,
    Municipio,
    ProblemaAlvo,
    Setor,
    Tecnologia,
    Tempo,
    TipoInovacao,
)
from core_admin.models.organizacoes import ContatoOrganizacao, Organizacao  # noqa: F401
from core_admin.models.projetos import ParticipanteProjeto, Projeto, TecnologiaProjeto  # noqa: F401
from core_admin.models.inovacao import Inovacao, TecnologiaInovacao  # noqa: F401
from core_admin.models.financeiro import InvestimentoInovacao  # noqa: F401
from core_admin.models.ecossistema import ConexaoEcossistema  # noqa: F401
from core_admin.models.pesquisa import CicloColeta, CoberturaColeta, UniversoPesquisado  # noqa: F401
from core_admin.models.adocao import AdocaoTecnologica  # noqa: F401
from core_admin.models.desempenho import DesempenhoOrganizacao, Talento  # noqa: F401
from core_admin.models.propriedade_intelectual import PropriedadeIntelectual  # noqa: F401
from core_admin.models.etl_historico import EtlExecucao, QuarentenaRegistro  # noqa: F401
