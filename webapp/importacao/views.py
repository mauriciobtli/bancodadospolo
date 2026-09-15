"""Tela de importação de dados.

Não reimplementa nenhuma lógica de carga: só chama etl/loaders e
etl/pipeline (o mesmo código, já testado, usado pelo ETL de linha de
comando). A conexão usada aqui é a role dedicada e mínima **web_import**
(WEB_IMPORT_DB_USER, via etl.db.get_web_import_engine() — ver
db/roles/web_import.sql) — nunca a role de administração do ETL
(POLO_DB_USER), que tem privilégio total sobre o schema e não deve rodar
dentro de um processo web exposto a upload de arquivo por usuário
autenticado. Também não é a role django_app: esta só tem SELECT em etl e
nenhum acesso a raw (ver db/roles/django_app.sql), insuficiente para
gravar a carga.
"""
from __future__ import annotations

import tempfile
from pathlib import Path

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import redirect, render
from django.urls import reverse

from etl.db import get_web_import_engine
from etl.pipeline import carregar_organizacoes_csv, carregar_organizacoes_xlsx, processar_organizacoes

from .forms import UploadArquivoForm

PERMISSAO_IMPORTAR = "core_admin.pode_importar_dados"


@login_required
@permission_required(PERMISSAO_IMPORTAR, raise_exception=True)
def importar_organizacoes(request):
    resultado = None

    if request.method == "POST":
        form = UploadArquivoForm(request.POST, request.FILES)
        if form.is_valid():
            resultado = _processar_upload(form.cleaned_data["arquivo"])
            if resultado["rejeitados"]:
                messages.warning(
                    request,
                    f"Importação concluída: {resultado['inseridos']} inserido(s), "
                    f"{resultado['atualizados']} atualizado(s), {resultado['rejeitados']} rejeitado(s). "
                    "Veja os detalhes em Importação → Quarentena.",
                )
            else:
                messages.success(
                    request,
                    f"Importação concluída sem rejeições: {resultado['inseridos']} inserido(s), "
                    f"{resultado['atualizados']} atualizado(s).",
                )
            return redirect(reverse("importacao:organizacoes"))
    else:
        form = UploadArquivoForm()

    return render(
        request,
        "importacao/organizacoes.html",
        {"form": form, "resultado": resultado, "titulo": "Importar organizações"},
    )


def _processar_upload(arquivo) -> dict:
    sufixo = Path(arquivo.name).suffix.lower()
    with tempfile.NamedTemporaryFile(suffix=sufixo, delete=False) as tmp:
        for pedaco in arquivo.chunks():
            tmp.write(pedaco)
        caminho_tmp = Path(tmp.name)

    engine = get_web_import_engine()
    try:
        with engine.begin() as conn:
            if sufixo == ".csv":
                execucao = carregar_organizacoes_csv(conn, caminho_tmp)
            else:
                execucao = carregar_organizacoes_xlsx(conn, caminho_tmp)

            processar_organizacoes(conn, execucao)
            status = "sucesso_parcial" if execucao.registros_rejeitados else "sucesso"
            execucao.finalizar(status=status)

            return {
                "id_execucao": execucao.id_execucao,
                "lidos": execucao.registros_lidos,
                "inseridos": execucao.registros_inseridos,
                "atualizados": execucao.registros_atualizados,
                "rejeitados": execucao.registros_rejeitados,
            }
    finally:
        caminho_tmp.unlink(missing_ok=True)
