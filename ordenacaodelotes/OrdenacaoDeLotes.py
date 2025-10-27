# -*- coding: utf-8 -*-
"""
OrganizadorDeLotes
A QGIS plugin to organize lots within a block.
"""
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QMessageBox
from qgis.gui import QgsMapToolIdentifyFeature
from qgis.core import (
    QgsProject, QgsVectorLayer, QgsFeature, QgsExpression,
    QgsProcessing, QgsProcessingFeedback, QgsMessageLog, Qgis)
from .resources import *
from .OrdenacaoDeLotes_dialog import OrganizadorDeLotesDialog
from .services.Notification import show_notification 
import os.path
import processing

class OrganizadorDeLotes:
    def __init__(self, iface):

        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.tool = None
        
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            f'ordenacaodelotes_{locale}.qm'
        )
        
        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)
        
        self.actions = []
        self.menu = self.tr(u'&OrganizadorDeLotes')
        self.first_start = None

    def tr(self, message):
        return QCoreApplication.translate('OrganizadorDeLotes', message)

    def add_action(self, icon_path, text, callback, enabled_flag=True, 
                   add_to_menu=True, add_to_toolbar=True, status_tip=None, 
                   whats_this=None, parent=None):
        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)
        
        if status_tip is not None:
            action.setStatusTip(status_tip)
        if whats_this is not None:
            action.setWhatsThis(whats_this)
        if add_to_toolbar:
            self.iface.addToolBarIcon(action)
        if add_to_menu:
            self.iface.addPluginToVectorMenu(self.menu, action)
            
        self.actions.append(action)
        return action

    def initGui(self):
        icon_path = os.path.join(self.plugin_dir, "icon.png")
        if not os.path.exists(icon_path):
            self._log(f"Ícone não encontrado em: {icon_path}", Qgis.Warning)
        self.add_action(
            icon_path,
            text=self.tr(u'Organiza Lote'),
            callback=self.run,
            parent=self.iface.mainWindow()
        )
        self.first_start = True

    def unload(self):
        for action in self.actions:
            self.iface.removePluginVectorMenu(self.tr(u'&OrganizadorDeLotes'), action)
            self.iface.removeToolBarIcon(action)

    def _log(self, message, level=Qgis.Info):
        """Helper para logging"""
        QgsMessageLog.logMessage(message, 'OrganizadorDeLotes', level)

    def _resetar_ferramenta_e_janela(self):
        """Reseta a ferramenta de seleção e traz a janela de diálogo para o primeiro plano"""
        if self.iface and self.dlg:
            self.dlg.activateWindow()
            self.dlg.raise_()
        if self.iface and self.tool:
            self.iface.mapCanvas().unsetMapTool(self.tool)
            self.iface.mainWindow().unsetCursor()
            self.tool = None

    def resetar_valores_plugin(self):
        """Reseta valores do plugin para estado inicial"""
        try:
            if self.tool and self.iface:
                self.iface.mapCanvas().unsetMapTool(self.tool)
                self.tool = None
            
            if self.iface:
                self.iface.mainWindow().unsetCursor()
                self.iface.mainWindow().statusBar().clearMessage()
            
            if self.dlg:
                if hasattr(self.dlg, 'lineOrdemPrimeira'):
                    self.dlg.lineOrdemPrimeira.setText('0')
                if hasattr(self.dlg, 'cmbConexao') and self.dlg.cmbConexao.count() > 0:
                    self.dlg.cmbConexao.setCurrentIndex(0)
            
            self._log("Valores resetados com sucesso")
        except Exception as e:
            self._log(f"Erro ao resetar valores: {e}", Qgis.Warning)

    def listar_conexoes_postgis(self):
        """Lista conexões PostgreSQL disponíveis"""
        settings = QSettings()
        settings.beginGroup('PostgreSQL/connections')
        conexoes = settings.childGroups()
        settings.endGroup()
        return conexoes

    def _get_quadra_layer(self):
        """Retorna camada Quadra se existir"""
        layers = QgsProject.instance().mapLayers().values()
        return next((layer for layer in layers if layer.name() == "Quadra"), None)

    def _get_lotes_layer(self):
        """Retorna camada de lotes se existir"""
        layers = QgsProject.instance().mapLayers().values()
        return next((layer for layer in layers 
                    if 'gis_boletim_lote' in layer.name().lower() or 'lote' in layer.name().lower()), None)

    def ativarFerramentaSelecao(self):
        """Ativa ferramenta de seleção de quadra no mapa"""
        if not self.iface or not self.dlg:
            return

        quadra_layer = self._get_quadra_layer()
        if not quadra_layer:
            show_notification("Aviso", "Camada 'Quadra' não encontrada!", "warning", 5000)
            return

        self.tool = QgsMapToolIdentifyFeature(self.iface.mapCanvas())
        self.tool.setLayer(quadra_layer)
        self.tool.featureIdentified.connect(self.capturarInsQuadra)
        self.iface.mapCanvas().setMapTool(self.tool)
        self.iface.mainWindow().setCursor(Qt.PointingHandCursor)
        
        show_notification("Ferramenta Ativa", "Clique no mapa para selecionar uma quadra", "info", 5000)

    def capturarInsQuadra(self, feature):
        """Captura ins_quadra da feature selecionada"""
        if not self.dlg or not feature.isValid():
            return
        if 'ins_quadra' in feature.fields().names():
            ins_quadra = feature['ins_quadra']
            show_notification("Quadra Selecionada", f"Quadra {ins_quadra} capturada com sucesso!", "success", 5000)
            if hasattr(self.dlg, 'lineInsQuadra'):
                self.dlg.lineInsQuadra.setText(str(ins_quadra))

        # Garante que a janela volte ao primeiro plano
            self._resetar_ferramenta_e_janela()

    def _filtrar_lotes_quadra(self, camada_lotes, ins_quadra):
        """Filtra lotes por quadra"""
        alg_params = {
            'FIELD': 'ins_quadra',
            'INPUT': camada_lotes,
            'OPERATOR': 0,
            'VALUE': str(ins_quadra),
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        return processing.run('native:extractbyattribute', alg_params)['OUTPUT']

    def contar_lotes_na_quadra(self, ins_quadra, tipo):
        """Conta e verifica lotes na quadra"""
        try:
            camada_lotes = self._get_lotes_layer()
            if not camada_lotes:
                raise Exception("Camada de lotes não encontrada!")

            camada_filtrada = self._filtrar_lotes_quadra(camada_lotes, ins_quadra)
            
            if tipo == 'OrganizarLotes':
                return sum(1 for f in camada_filtrada.getFeatures() 
                          if f['matricula'] is not None and f['matricula'] != '')
            else:
                for feature in camada_filtrada.getFeatures():
                    if feature['matricula'] is not None and feature['matricula'] != '':
                        return feature['ordem'] != feature['nv_ordem']
                return False

        except Exception as e:
            self._log(f"Erro ao contar lotes: {e}", Qgis.Critical)
            return 0 if tipo == 'OrganizarLotes' else False

    def verificar_ins_quadra_existe(self, conexao, ins_quadra):
        """Verifica se ins_quadra existe na tabela novaordem"""
        try:
            sql = f'''
                SELECT 1 as existe
                FROM comercial_umc.novaordem
                WHERE ins_quadra = {ins_quadra}
                LIMIT 1
            '''
            alg_params = {
                'DATABASE': conexao,
                'SQL': sql,
                'OUTPUT': 'memory:temp_verificacao'
            }
            
            result = processing.run('native:postgisexecuteandloadsql', alg_params)
            existe = result['OUTPUT'].featureCount() > 0
            self._log(f"Verificação ins_quadra {ins_quadra}: {'encontrado' if existe else 'não encontrado'}")
            return existe

        except Exception as e:
            self._log(f"Erro ao verificar ins_quadra {ins_quadra}: {e}", Qgis.Warning)
            try:
                sql_check = f'''
                    DO $$
                    DECLARE rec_count INTEGER;
                    BEGIN
                        SELECT COUNT(*) INTO rec_count
                        FROM comercial_umc.novaordem
                        WHERE ins_quadra = {ins_quadra};
                        IF rec_count = 0 THEN
                            RAISE EXCEPTION 'NO_RECORDS_FOUND';
                        END IF;
                    END $$;
                '''
                processing.run('native:postgisexecutesql', {'DATABASE': conexao, 'SQL': sql_check})
                return True
            except Exception as e2:
                return 'no_records_found' not in str(e2).lower()

    def excluir_ins_quadra_existente(self, conexao, ins_quadra):
        """Exclui registros da quadra na tabela novaordem"""
        try:
            sql = f'DELETE FROM comercial_umc.novaordem WHERE ins_quadra = {ins_quadra}'
            processing.run('native:postgisexecutesql', {'DATABASE': conexao, 'SQL': sql})
            self._log(f"Registros da quadra {ins_quadra} excluídos com sucesso")
            return True
        except Exception as e:
            self._log(f"Erro ao excluir registros: {e}", Qgis.Critical)
            return False

    def _preparar_campos_refactor(self, ordem_expr='ordem'):
        """Prepara mapeamento de campos para refactor"""
        return [
            {'expression': '"matricula"', 'length': -1, 'name': 'matricula', 'precision': 0, 'type': 2},
            {'expression': '"ins_quadra"', 'length': -1, 'name': 'ins_quadra', 'precision': 0, 'type': 2},
            {'expression': f'"{ordem_expr}"', 'length': -1, 'name': 'n_ordem', 'precision': 0, 'type': 4}
        ]

    def _importar_para_postgis(self, conexao, camada):
        """Importa camada para PostgreSQL"""
        alg_params = {
            'ADDFIELDS': False,
            'APPEND': True,
            'A_SRS': 'EPSG:31984',
            'DATABASE': conexao,
            'GEOCOLUMN': '',
            'INPUT': camada,
            'LAUNDER': False,
            'OVERWRITE': False,
            'PK': 'id',
            'PRECISION': True,
            'PROMOTETOMULTI': True,
            'SCHEMA': 'comercial_umc',
            'TABLE': 'novaordem'
        }
        processing.run('gdal:importvectorintopostgisdatabaseavailableconnections', alg_params)

    def restaurar_ordem_original(self, conexao, ins_quadra):
        """Restaura ordem original dos lotes"""
        try:
            camada_lotes = self._get_lotes_layer()
            if not camada_lotes:
                raise Exception("Camada de lotes não encontrada!")

            camada_filtrada = self._filtrar_lotes_quadra(camada_lotes, ins_quadra)

            alg_params = {
                'FIELDS_MAPPING': self._preparar_campos_refactor(),
                'INPUT': camada_filtrada,
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            }
            camada_processada = processing.run('native:refactorfields', alg_params)['OUTPUT']

            self._importar_para_postgis(conexao, camada_processada)

            return {'success': True, 'message': 'Ordem original restaurada com sucesso!'}
        except Exception as e:
            self._log(f"Erro ao restaurar ordem: {e}", Qgis.Critical)
            return {'success': False, 'message': f"Erro: {e}"}

    def organizar_ordem_lote(self, conexao, ins_quadra, ordem_primeira):
        """Organiza ordem dos lotes"""
        try:
            camada_lotes = self._get_lotes_layer()
            if not camada_lotes:
                raise Exception("Camada de lotes não encontrada!")

            camada_filtrada = self._filtrar_lotes_quadra(camada_lotes, ins_quadra)

            offset = sum(1 for f in camada_filtrada.getFeatures() if f['ordem'] >= ordem_primeira)

            ordem_expr = f'''
                CASE
                    WHEN "ordem" >= {ordem_primeira} THEN "ordem" - ({ordem_primeira} - 1)
                    WHEN "ordem" < {ordem_primeira} THEN "ordem" + {offset}
                END
            '''

            campos = self._preparar_campos_refactor()
            campos[2]['expression'] = ordem_expr
            
            alg_params = {
                'FIELDS_MAPPING': campos,
                'INPUT': camada_filtrada,
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            }
            camada_processada = processing.run('native:refactorfields', alg_params)['OUTPUT']

            self._importar_para_postgis(conexao, camada_processada)

            return {'success': True, 'message': 'Nova ordem atualizada com sucesso!'}
        except Exception as e:
            self._log(f"Erro ao organizar ordem: {e}", Qgis.Critical)
            return {'success': False, 'message': f"Erro: {e}"}

    def _validar_entrada_organizacao(self, conexao, ins_quadra, ordem_primeira):
        """Valida entradas antes de organizar"""
        if not conexao:
            show_notification("Aviso", "Selecione uma conexão PostgreSQL!", "warning", 5000)
            self._resetar_ferramenta_e_janela()
            return False

        if not ins_quadra or ins_quadra == '99' or not ins_quadra.isdigit():
            show_notification("Aviso", "Selecione uma quadra válida!", "warning", 5000)
            self._resetar_ferramenta_e_janela()
            return False

        if ordem_primeira < 1:
            show_notification("Aviso", "A ordem deve ser maior que 0!", "warning", 5000)
            self._resetar_ferramenta_e_janela()
            return False

        return True

    def executar_organizacao(self):
        """Executa organização dos lotes"""
        try:
            conexao = self.dlg.cmbConexao.currentText()
            ins_quadra = self.dlg.lineInsQuadra.text()
            
            if not self.dlg.lineOrdemPrimeira.text():
                show_notification("Aviso", "Informe a nova ordem!", "warning", 5000)
                self._resetar_ferramenta_e_janela()
                return
            
            ordem_primeira = int(self.dlg.lineOrdemPrimeira.text())

            if not self._validar_entrada_organizacao(conexao, ins_quadra, ordem_primeira):
                return

            num_lotes = self.contar_lotes_na_quadra(ins_quadra, 'OrganizarLotes')
            if num_lotes == 0:
                show_notification("Aviso", "Nenhum lote encontrado!", "warning", 5000)
                self._resetar_ferramenta_e_janela()
                return

            if ordem_primeira > num_lotes:
                show_notification(
                    "Aviso",
                    f"Ordem inicial ({ordem_primeira}) maior que número de lotes ({num_lotes})!",
                    "warning",
                    4000
                )
                self._resetar_ferramenta_e_janela()
                return

            resposta = QMessageBox.question(
                self.dlg, "Confirmar Operação",
                f"Reorganizar lotes da quadra {ins_quadra} a partir da ordem {ordem_primeira}?\n\n"
                f"ATENÇÃO: Registros existentes serão substituídos!",
                QMessageBox.Yes | QMessageBox.No
            )

            if resposta == QMessageBox.No:
                return

            show_notification("Processando", "Reorganizando lotes...", "info", 2000)

            if not self.excluir_ins_quadra_existente(conexao, ins_quadra):
                show_notification("Erro", "Erro ao excluir registros existentes!", "error", 4000)
                return

            resultado = self.organizar_ordem_lote(conexao, ins_quadra, ordem_primeira)
            
            if resultado['success']:
                show_notification(
                    "Sucesso!",
                    f"Quadra {ins_quadra} reorganizada com sucesso!",
                    "success",
                    3500
                )
                self.dlg.close()
            else:
                show_notification("Erro", resultado['message'], "error", 4000)

        except Exception as e:
            show_notification("Erro", f"Erro na execução: {str(e)}", "error", 4000)
            self._log(f"Erro na execução: {e}", Qgis.Critical)

    def executar_exclusao_novaordem(self):
        """Exclui novaordem e restaura ordem original"""
        try:
            conexao = self.dlg.cmbConexao.currentText()
            ins_quadra_text = self.dlg.lineInsQuadra.text()
            ins_quadra = int(ins_quadra_text) if ins_quadra_text.isdigit() else 0

            if not conexao:
                show_notification("Aviso", "Selecione uma conexão PostgreSQL!", "warning", 5000)
                self._resetar_ferramenta_e_janela()
                return

            if ins_quadra in (0, 99):
                show_notification("Aviso", "Selecione uma quadra válida!", "warning", 5000)
                self._resetar_ferramenta_e_janela()
                return

            if not self.contar_lotes_na_quadra(ins_quadra, 'Reorganizar'):
                show_notification(
                    "Aviso",
                    f"A quadra {ins_quadra} já está com a ordem original!",
                    "warning",
                    4000
                )
                self._resetar_ferramenta_e_janela()
                return

            resposta = QMessageBox.question(
                self.dlg, "Confirmar Exclusão e Restauração",
                f"Você deseja restaurar a ordem da quadra ({ins_quadra}) para a ordem original?\n\n"
                f"ATENÇÃO: Será preenchida com valores do campo 'ordem' original!",
                QMessageBox.Yes | QMessageBox.No
            )

            if resposta == QMessageBox.No:
                return

            show_notification("Processando", "Restaurando ordem original...", "info", 2000)

            if not self.excluir_ins_quadra_existente(conexao, ins_quadra):
                show_notification("Erro", "Erro ao excluir registros!", "error", 4000)
                self._resetar_ferramenta_e_janela()
                return

            resultado = self.restaurar_ordem_original(conexao, ins_quadra)
            
            if resultado['success']:
                show_notification(
                    "Sucesso!",
                    f"Quadra {ins_quadra} restaurada para ordem original!",
                    "success",
                    5000
                )
                self.dlg.close()
            else:
                show_notification("Erro", resultado['message'], "error", 4000)

        except Exception as e:
            show_notification("Erro", f"Erro na execução: {str(e)}", "error", 4000)
            self._log(f"Erro: {e}", Qgis.Critical)

    def run (self):
        """Processa o algoritmo principal"""
        self.resetar_valores_plugin()

        if self.first_start:
            self.first_start = False
            self.dlg = OrganizadorDeLotesDialog()

            # Conectar botão de seleção
            if hasattr(self.dlg, 'btnSelecionarQuadra') and self.iface:
                self.dlg.btnSelecionarQuadra.clicked.connect(self.ativarFerramentaSelecao)

            # Carregar conexões
            if hasattr(self.dlg, 'cmbConexao'):
                self.dlg.cmbConexao.clear()
                conexoes = self.listar_conexoes_postgis()
                if not conexoes:
                    show_notification(
                        "Aviso",
                        "Nenhuma conexão PostgreSQL encontrada!",
                        "warning",
                        4000
                    )
                    return {}
                self.dlg.cmbConexao.addItems(conexoes)

            # Conectar botões
            if hasattr(self.dlg, 'btnExecutar'):
                self.dlg.btnExecutar.clicked.connect(self.executar_organizacao)
            
            if hasattr(self.dlg, 'btnExcluirNovaOrdem'):
                self.dlg.btnExcluirNovaOrdem.clicked.connect(self.executar_exclusao_novaordem)

        self.dlg.show()
        if hasattr(self.dlg, 'exec_'):
            self.dlg.exec_()
        
        return {}