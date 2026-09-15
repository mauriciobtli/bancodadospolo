"""AdminSite customizado: marca/idioma do Observatorio Polo Inovale.

Sem app/tema novo — e o Django Admin padrao, so com titulo e agrupamento
de menu ajustados para o vocabulario do Polo Inovale (prioridade do
projeto: simplicidade de uso, nao aparencia sofisticada).
"""
from __future__ import annotations

import functools

from django.contrib import messages
from django.contrib.admin import AdminSite
from django.db import IntegrityError
from django.http import HttpResponseRedirect

from core_admin.erros import mensagem_amigavel


_GRUPOS_MENU = [
    ("Organizações", ["Organizacao", "ContatoOrganizacao", "Municipio", "Setor"]),
    ("Projetos", ["Projeto", "ParticipanteProjeto", "TecnologiaProjeto", "FonteRecurso", "ProblemaAlvo", "Tecnologia"]),
    ("Inovação", ["Inovacao", "TecnologiaInovacao", "TipoInovacao", "GrauNovidade"]),
    ("Financeiro", ["InvestimentoInovacao"]),
    ("Ecossistema", ["ConexaoEcossistema"]),
    ("Adoção Tecnológica", ["AdocaoTecnologica"]),
    ("Desempenho e Talentos", ["DesempenhoOrganizacao", "Talento"]),
    ("Propriedade Intelectual", ["PropriedadeIntelectual"]),
    ("Pesquisa (Ciclos de Coleta)", ["CicloColeta"]),
    ("Importação", ["EtlExecucao", "QuarentenaRegistro"]),
]


class PoloInovaleAdminSite(AdminSite):
    site_header = "Observatório Polo Inovale"
    site_title = "Polo Inovale"
    index_title = "Painel administrativo"
    empty_value_display = "—"

    def admin_view(self, view, cacheable=False):
        """Envolve toda view do admin: se o Postgres rejeitar um SAVE
        (CHECK, UNIQUE, FK ou trigger de guarda — ver db/schemas/*.sql), o
        usuário vê uma mensagem clara em vez de uma página de erro 500.
        Nenhuma regra nova é validada aqui: só se traduz o que o banco já
        rejeitou. Os dados digitados são perdidos nesse caso (a página
        recarrega em branco) — aceitável para um erro que já é raro, já
        que a maioria dos domínios/formatos é validada antes de chegar
        aqui (choices do formulário, clean() do modelo)."""
        view_original = super().admin_view(view, cacheable=cacheable)

        @functools.wraps(view_original)
        def view_com_erro_amigavel(request, *args, **kwargs):
            try:
                return view_original(request, *args, **kwargs)
            except IntegrityError as exc:
                messages.error(request, f"Não foi possível salvar: {mensagem_amigavel(exc)}")
                return HttpResponseRedirect(request.get_full_path())

        return view_com_erro_amigavel

    def get_app_list(self, request, app_label=None):
        """Reagrupa os modelos (todos no mesmo app Django `core_admin`) em
        secoes tematicas no menu, em vez da lista alfabetica padrao — pura
        organizacao de UI, nao afeta permissoes nem dados."""
        apps_originais = super().get_app_list(request, app_label)
        modelos_por_nome = {m["object_name"]: m for app in apps_originais for m in app["models"]}

        secoes = []
        usados: set[str] = set()
        for nome_secao, nomes_modelos in _GRUPOS_MENU:
            modelos_da_secao = [modelos_por_nome[n] for n in nomes_modelos if n in modelos_por_nome]
            usados.update(nomes_modelos)
            if modelos_da_secao:
                secoes.append(
                    {
                        "name": nome_secao,
                        "app_label": nome_secao.lower().replace(" ", "_"),
                        "app_url": "#",
                        "has_module_perms": True,
                        "models": modelos_da_secao,
                    }
                )

        restantes = [m for nome, m in modelos_por_nome.items() if nome not in usados]
        if restantes:
            secoes.append(
                {"name": "Outros", "app_label": "outros", "app_url": "#", "has_module_perms": True, "models": restantes}
            )
        return secoes


site = PoloInovaleAdminSite(name="polo_admin")
