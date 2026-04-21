# jira_api.py
"""
Jira-API-Client.

Erbt von :class:`base_api.RestAPIClient` und implementiert nur die
Jira-spezifischen Endpunkte.
"""

from __future__ import annotations
from typing import Any, Dict
import json

from base_api import RestAPIClient

class JiraAPI(RestAPIClient):
    """
    Client für Jira Core.
    Diese Klasse implementiert nur die Jira-spezifischen Endpunkte.
    Erbt von :class:`base_api.RestAPIClient`.
    """

    API_PATH = "rest/api/2/"

    def __init__(
        self,
        base_url: str,
        prefix: str,
        user: str,
        password: str,
        *,
        proxies=None,
    ) -> None:
        super().__init__(base_url, user, password, proxies=proxies)
        self._prefix = prefix

    # --------------------------------------------------------------- #
    # Util                                                            #
    # --------------------------------------------------------------- #
    def normalize_issue_key(self, key:str):
        """
        Normalisiert den übergebenen Issue-Key.
        Fügt das Projekt-Präfix hinzu, falls es noch nicht vorhanden ist.
        
        :param key: Der ursprüngliche Issue-Key (mit oder ohne Präfix).
        :return: Der vollständige Issue-Key (z.B. "PROJ-123").
        """
        issueKey = f'{key}'
        if not issueKey.startswith(self._prefix):
            issueKey = f'{self._prefix}-{issueKey}'
        return issueKey
    

    # --------------------------------------------------------------- #
    # Endpunkte                                                      #
    # --------------------------------------------------------------- #

    # GET
    def get_project_info(self):
        """         
        Ruft die detaillierten Informationen zum konfigurierten Projekt (anhand des Präfixes) ab.  
        :return: Response-Objekt der GET-Anfrage.
        """
        return self.get(f"{self.API_PATH}project/{self._prefix}")

    def get_issue_info(self, key: str):
        """
        Ruft die Informationen zu einem Issue ab.    
        :param key: Der Key des Issues (mit oder ohne Projekt-Präfix).
        :return: Response-Objekt der GET-Anfrage.
        """
        return self.get(f"{self.API_PATH}issue/{self.normalize_issue_key(key)}")

    def get_changelogs(self, key: str):
        """     
        Ruft die Änderungsprotokolle (Changelogs) eines Issues ab.
        :param key: Der Key des Issues (mit oder ohne Projekt-Präfix).
        :return: Response-Objekt der GET-Anfrage.
        """
        return self.get(f"{self.API_PATH}issue/{self.normalize_issue_key(key)}/changelog")

    def check_issue_editable_fields(self, key: str):
        """
        Prüft, welche Felder eines Issues bearbeitet werden können.
        :param key: Der Key des Issues (mit oder ohne Projekt-Präfix).
        :return: Response-Objekt der GET-Anfrage.
        """
        return self.get(f"{self.API_PATH}issue/{self.normalize_issue_key(key)}/editmeta")

    def get_all_fields(self):
        """
        Ruft alle verfügbaren Felder ab.        
        :return: Response-Objekt der GET-Anfrage.
        """
        return self.get(f"{self.API_PATH}field")

    def get_field_reference_data(self):
        """
        Ruft die Referenzdaten für alle Felder ab.      
        :return: Response-Objekt der GET-Anfrage.
        """
        return self.get(f"{self.API_PATH}jql/autocompletedata")

    def jql_requests(self, jql: str, max_results: int = 50):
        """
        Führt eine JQL-Abfrage aus und gibt die Ergebnisse zurück.
        :param jql: JQL-Abfrage-String.
        :param max_results: Maximale Anzahl der Ergebnisse (Standard: 50).
        :return: Response-Objekt der GET-Anfrage mit den Suchergebnissen.
        """         
        return self.get(f"{self.API_PATH}search?jql={jql}&maxResults={max_results}")
    
    def get_bugs_linked_to_test(self, test_id: str):
        """
        Sucht nach Bugs, die mit einem bestimmten Testfall verknüpft sind.
        :param test_id: Der Key des Testfalls.
        :return: Response-Objekt der GET-Anfrage mit den gefundenen Bugs.
        """
        jql = (
            f'issue in linkedIssues("{self.normalize_issue_key(test_id)}") '
            'AND issuetype = Bug'
        )
        return self.jql_requests(jql)

    def get_test_cases_in_project(self):
        """
        Ruft alle Testfälle (Issues vom Typ 'Test') im aktuell konfigurierten Projekt ab.
        :return: Response-Objekt der GET-Anfrage mit den Testfällen.
        """
        jql = f'project = "{self._prefix}" AND issuetype = Test'
        return self.jql_requests(jql)

    def get_all_transitions(self, key:str):
        """
        Ruft alle möglichen Statusübergänge (Transitions) für ein bestimmtes Issue ab.
        :param key: Der Key des Issues (mit oder ohne Projekt-Präfix).
        :return: Response-Objekt der GET-Anfrage mit den Transitions.
        """
        return self.get(f"{self.API_PATH}issue/{self.normalize_issue_key(key)}/transitions")
        
    # POST
    def create_issue(self, data: Dict[str, Any]):
        """
        Erstellt ein neues Issue.       
        :param data: Die zu erstellenden Felder im JSON-Format.
        :return: Response-Objekt der POST-Anfrage.
        """
        return self.post(f"{self.API_PATH}issue", data=data)

    def set_issue_transition(self, key: Any, data: Dict[str, Any]):
        """
        Führt einen Statusübergang (Transition) für ein Issue aus.
        :param key: Der Key des Issues.
        :param data: JSON-Payload mit der Transition-ID.
                     Beispiel: {'transition': {'id': '4'}}
                     (Die ID hängt vom konfigurierten Workflow ab).
        :return: Response-Objekt der POST-Anfrage.
        """
        return self.post(f"{self.API_PATH}issue/{self.normalize_issue_key(key)}/transitions", data=data)
    
    def set_issuelink(self, data):
        """
        Erstellt eine Verknüpfung (Link) zwischen zwei Issues.
        :param data: JSON-Payload mit Link-Typ und den beiden Issue-Keys (inward/outward).
                     Beispiel:
                     {
                         "type": {"name": "Befund"},
                         "inwardIssue": {"key": "STORY-123"},
                         "outwardIssue": {"key": "TEST-456"}
                     }
        :return: Response-Objekt der POST-Anfrage.
        """
        return self.post(f"{self.API_PATH}issueLink", data=data)

    # PUT
    def update_issue(self, key: str, data: Dict[str, Any]):
        """
        Aktualisiert die Felder eines bestehenden Issues.
        :param key: Der Key des Issues (mit oder ohne Projekt-Präfix).
        :param data: Die zu aktualisierenden Felder im JSON-Format.
        :return: Response-Objekt der PUT-Anfrage.
        """
        return self.put(f"{self.API_PATH}issue/{self.normalize_issue_key(key)}", data=data)
    
    # DELETE
    def delete_issue(self, key: str):
        """
        Löscht ein Issue.
        :param key: Der Key des Issues (mit oder ohne Projekt-Präfix).
        :return: Response-Objekt der DELETE-Anfrage.
        """
        return self.delete(f"{self.API_PATH}issue/{self.normalize_issue_key(key)}")
    
    # Sonstiges
    def check_user_credentials(self):
        """
        Prüft Benutzer daten durch einen simplen GET-Call auf die API-Wurzel.
        Gibt das Response-Objekt zurück (Status 200 → OK).
        """
        return self.get(self.API_PATH)

if __name__ == '__main__':
    pass
