# tools.py
"""
Define las herramientas de LangChain para interactuar con Jira y Xray.
Utiliza un patrón de factoría para inyectar las instancias de JiraAPI y XrayAPI.
"""

import sys
import os
from typing import List, Dict, Any, Optional
from langchain_core.tools import tool, BaseTool

# Asegurar que el directorio src/api esté en el path para poder importar base_api, jira_api y xray_api
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
api_dir = os.path.join(parent_dir, "api")
if api_dir not in sys.path:
    sys.path.insert(0, api_dir)

from jira_api import JiraAPI
from xray_api import XrayAPI

def get_jira_tools(jira: JiraAPI, xray: Optional[XrayAPI] = None) -> List[BaseTool]:
    """
    Retorna la lista de herramientas de LangChain enlazadas con los clientes de la API.
    """

    @tool
    def get_project_info() -> str:
        """
        Obtiene información general y configuración del proyecto de Jira actual.
        """
        response = jira.get_project_info()
        if response.ok:
            return response.text
        return f"Error al obtener información del proyecto: {response.status_code} - {response.text}"

    @tool
    def get_issue_info(key: str) -> str:
        """
        Obtiene todos los detalles, campos y estado de un issue específico en Jira por su clave (por ejemplo: 'PROJ-123' o solo '123').
        """
        response = jira.get_issue_info(key)
        if response.ok:
            return response.text
        return f"Error al obtener información del issue {key}: {response.status_code} - {response.text}"

    @tool
    def get_issue_changelogs(key: str) -> str:
        """
        Obtiene el historial de cambios (changelogs) de un issue de Jira por su clave.
        """
        response = jira.get_changelogs(key)
        if response.ok:
            return response.text
        return f"Error al obtener changelogs del issue {key}: {response.status_code} - {response.text}"

    @tool
    def check_issue_editable_fields(key: str) -> str:
        """
        Verifica qué campos de un issue específico son editables en su estado actual.
        """
        response = jira.check_issue_editable_fields(key)
        if response.ok:
            return response.text
        return f"Error al verificar campos editables para {key}: {response.status_code} - {response.text}"

    @tool
    def get_all_fields() -> str:
        """
        Obtiene la lista de todos los campos disponibles en la instancia de Jira (tanto del sistema como personalizados).
        """
        response = jira.get_all_fields()
        if response.ok:
            return response.text
        return f"Error al obtener todos los campos: {response.status_code} - {response.text}"

    @tool
    def jql_search(query: str, max_results: int = 50) -> str:
        """
        Realiza una búsqueda de issues utilizando JQL (Jira Query Language).
        Ejemplo de query: 'project = "PROJ" AND status = "To Do" AND assignee = currentUser()'
        """
        response = jira.jql_requests(query, max_results=max_results)
        if response.ok:
            return response.text
        return f"Error al ejecutar búsqueda JQL: {response.status_code} - {response.text}"

    @tool
    def get_bugs_linked_to_test(test_id: str) -> str:
        """
        Busca bugs que estén enlazados a un caso de prueba (Test Case) específico.
        """
        response = jira.get_bugs_linked_to_test(test_id)
        if response.ok:
            return response.text
        return f"Error al buscar bugs asociados al test {test_id}: {response.status_code} - {response.text}"

    @tool
    def get_test_cases_in_project() -> str:
        """
        Obtiene todos los casos de prueba (issues de tipo 'Test') en el proyecto configurado.
        """
        response = jira.get_test_cases_in_project()
        if response.ok:
            return response.text
        return f"Error al obtener casos de prueba: {response.status_code} - {response.text}"

    @tool
    def get_issue_transitions(key: str) -> str:
        """
        Obtiene los estados de destino disponibles (transiciones) para un issue.
        Retorna los IDs de las transiciones y sus nombres.
        """
        response = jira.get_all_transitions(key)
        if response.ok:
            return response.text
        return f"Error al obtener transiciones para {key}: {response.status_code} - {response.text}"

    @tool
    def create_jira_issue(summary: str, description: str, issue_type: str = "Test", priority: Optional[str] = None) -> str:
        """
        Crea un nuevo issue en el proyecto configurado de Jira.
        Parámetros:
        - summary: El título/resumen del issue.
        - description: La descripción del issue.
        - issue_type: El tipo de issue (por ejemplo: 'Task', 'Bug', 'Story', 'Test'). Por defecto es 'Task'.
        - priority: La prioridad (por ejemplo: 'High', 'Medium', 'Low'). Opcional.
        """
        data = {
            "fields": {
                "project": {"key": jira._prefix},
                "summary": summary,
                "description": description,
                "issuetype": {"name": issue_type}
            }
        }
        if priority:
            data["fields"]["priority"] = {"name": priority}
            
        response = jira.create_issue(data)
        if response.ok:
            return f"Issue creado con éxito:\n{response.text}"
        return f"Error al crear el issue: {response.status_code} - {response.text}"

    @tool
    def transition_jira_issue(key: str, transition_id: str) -> str:
        """
        Cambia el estado de un issue de Jira (transición).
        Deberás usar get_issue_transitions previamente para saber la ID de transición correspondiente.
        """
        data = {"transition": {"id": transition_id}}
        response = jira.set_issue_transition(key, data)
        if response.ok:
            return f"El issue {key} se ha transitado con éxito a la transición ID {transition_id}."
        return f"Error al transitar el issue {key}: {response.status_code} - {response.text}"

    @tool
    def link_jira_issues(inward_key: str, outward_key: str, link_type_name: str = "Befund") -> str:
        """
        Crea un enlace entre dos issues de Jira.
        Ejemplo: Enlazar una Story con un Test, o un Bug con una Story.
        Parámetros:
        - inward_key: Clave del issue destino.
        - outward_key: Clave del issue origen.
        - link_type_name: Nombre del tipo de enlace. Por defecto es 'Befund'.
        """
        data = {
            "type": {"name": link_type_name},
            "inwardIssue": {"key": jira.normalize_issue_key(inward_key)},
            "outwardIssue": {"key": jira.normalize_issue_key(outward_key)}
        }
        response = jira.set_issuelink(data)
        if response.ok:
            return f"Enlace tipo '{link_type_name}' creado exitosamente entre {inward_key} y {outward_key}."
        return f"Error al crear enlace: {response.status_code} - {response.text}"

    @tool
    def update_jira_issue(key: str, summary: Optional[str] = None, description: Optional[str] = None, assignee: Optional[str] = None) -> str:
        """
        Actualiza los campos básicos de un issue de Jira (como el resumen, la descripción o el responsable).
        Nota: Para cambiar de estado usa transition_jira_issue.
        Parámetros:
        - key: La clave del issue.
        - summary: Nuevo título. Opcional.
        - description: Nueva descripción. Opcional.
        - assignee: Nombre del usuario responsable. Opcional.
        """
        fields = {}
        if summary is not None:
            fields["summary"] = summary
        if description is not None:
            fields["description"] = description
        if assignee is not None:
            fields["assignee"] = {"name": assignee}

        if not fields:
            return "No se especificaron campos para actualizar."

        data = {"fields": fields}
        response = jira.update_issue(key, data)
        if response.ok:
            return f"Issue {key} actualizado correctamente."
        return f"Error al actualizar el issue {key}: {response.status_code} - {response.text}"

    @tool
    def delete_jira_issue(key: str) -> str:
        """
        Elimina un issue de Jira por su clave. Use con precaución.
        """
        response = jira.delete_issue(key)
        if response.ok:
            return f"Issue {key} eliminado con éxito."
        return f"Error al eliminar el issue {key}: {response.status_code} - {response.text}"

    # Lista básica de herramientas de Jira Core
    tools_list = [
        get_project_info,
        get_issue_info,
        get_issue_changelogs,
        check_issue_editable_fields,
        get_all_fields,
        jql_search,
        get_bugs_linked_to_test,
        get_test_cases_in_project,
        get_issue_transitions,
        create_jira_issue,
        transition_jira_issue,
        link_jira_issues,
        update_jira_issue,
    ]

    # Agregar herramientas de Xray si el cliente está provisto
    if xray is not None:
        @tool
        def xray_get_test_steps(test_id: str) -> str:
            """
            [XRAY] Obtiene los pasos detallados de un caso de prueba (Test) específico.
            """
            response = xray.get_test_steps(test_id)
            if response.ok:
                return response.text
            return f"Error al obtener pasos de prueba para {test_id}: {response.status_code} - {response.text}"

        @tool
        def xray_add_test_step(test_id: str, step: str, data: str, result: str) -> str:
            """
            [XRAY] Agrega un paso de prueba a un Test.
            Parámetros:
            - test_id: Clave del Test.
            - step: Descripción de la acción del paso.
            - data: Datos de entrada para el paso.
            - result: Resultado esperado del paso.
            """
            payload = {
                "step": step,
                "data": data,
                "result": result
            }
            response = xray.add_test_step(test_id, payload)
            if response.ok:
                return f"Paso agregado con éxito al Test {test_id}."
            return f"Error al agregar paso al Test {test_id}: {response.status_code} - {response.text}"

        @tool
        def xray_delete_test_step(test_id: str, step_id: str) -> str:
            """
            [XRAY] Elimina un paso de prueba específico de un Test.
            """
            response = xray.delete_step(test_id, step_id)
            if response.ok:
                return f"Paso {step_id} del Test {test_id} eliminado con éxito."
            return f"Error al eliminar paso {step_id}: {response.status_code} - {response.text}"

        @tool
        def xray_get_all_test_executions(test_id: str) -> str:
            """
            [XRAY] Obtiene la lista de todas las ejecuciones de prueba (Test Executions) asociadas a un Test.
            """
            response = xray.get_all_test_executions(test_id)
            if response.ok:
                return response.text
            return f"Error al obtener ejecuciones de prueba para {test_id}: {response.status_code} - {response.text}"

        @tool
        def xray_get_test_run_results(test_id: str) -> str:
            """
            [XRAY] Obtiene los resultados de ejecución (Test Runs) asociados a un Test.
            """
            response = xray.get_test_run_results(test_id)
            if response.ok:
                return response.text
            return f"Error al obtener resultados de ejecución para {test_id}: {response.status_code} - {response.text}"

        @tool
        def xray_add_test_to_execution(execution_id: str, test_keys: List[str]) -> str:
            """
            [XRAY] Agrega una lista de claves de test (por ejemplo: ['PROJ-101', 'PROJ-102']) a una ejecución de prueba (Test Execution).
            """
            payload = {"add": test_keys}
            response = xray.add_test_to_test_execution(execution_id, payload)
            if response.ok:
                return f"Tests {test_keys} agregados correctamente a la ejecución {execution_id}."
            return f"Error al agregar tests a la ejecución {execution_id}: {response.status_code} - {response.text}"

        @tool
        def xray_update_testrun_status(testrun_id: str, status: str) -> str:
            """
            [XRAY] Actualiza el estado de una ejecución de prueba (Test Run) por su ID.
            El status debe ser uno de los configurados (por ejemplo: 'PASS', 'FAIL', 'TODO', 'EXECUTING').
            """
            payload = {"status": status}
            response = xray.update_testrun(testrun_id, payload)
            if response.ok:
                return f"El estado del Test Run {testrun_id} se ha actualizado a {status}."
            return f"Error al actualizar estado del Test Run {testrun_id}: {response.status_code} - {response.text}"

        @tool
        def xray_get_testrun_data(execution_id: str, test_id: str) -> str:
            """
            [XRAY] Obtiene los datos detallados de un Test Run específico dada la clave de ejecución y el ID del Test.
            """
            response = xray.get_test_run_data(execution_id, test_id)
            if response.ok:
                return response.text
            return f"Error al obtener datos del Test Run: {response.status_code} - {response.text}"

        @tool
        def xray_get_testrun_data_by_id(testrun_id: str) -> str:
            """
            [XRAY] Obtiene los datos detallados de un Test Run por su ID, incluyendo iteraciones y pasos si aplica.
            """
            response = xray.get_test_run_data_by_id(testrun_id)
            if response.ok:
                return response.text
            return f"Error al obtener datos del Test Run {testrun_id}: {response.status_code} - {response.text}"

        @tool
        def xray_upload_results(payload: Dict[str, Any]) -> str:
            """
            [XRAY] Importa/Sube resultados de pruebas automáticas a Xray usando el formato JSON de ejecución de Xray.
            """
            success = xray.upload_results(payload)
            if success:
                return "Resultados de pruebas importados con éxito a Xray."
            return "Error al importar los resultados de pruebas a Xray."

        # Añadir herramientas al listado
        tools_list.extend([
            xray_get_test_steps,
            xray_add_test_step,
            xray_delete_test_step,
            xray_get_all_test_executions,
            xray_get_test_run_results,
            xray_add_test_to_execution,
            xray_update_testrun_status,
            xray_get_testrun_data,
            xray_get_testrun_data_by_id,
            xray_upload_results
        ])

    return tools_list
