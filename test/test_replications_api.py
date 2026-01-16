import asyncio
import hashlib
import os
import unittest
from datetime import datetime, timedelta
from unittest import IsolatedAsyncioTestCase

from iikoserver_client import ApiClient, Configuration
from iikoserver_client.api.corporation_management_api import CorporationManagementApi
from iikoserver_client.api.replications_api import ReplicationsApi
from iikoserver_client.api.session_management_api import SessionManagementApi
from iikoserver_client.models.replication_status_dto import ReplicationStatusDto
from iikoserver_client.models.server_type_enum import ServerTypeEnum


class TestReplicationsApi(IsolatedAsyncioTestCase):
    """Тестирование API управления репликациями"""

    async def asyncSetUp(self) -> None:
        """Настройка перед каждым тестом"""
        # Read credentials from env variables or set them directly
        self.server_url = os.environ.get("IIKO_SERVER_URL", None)
        self.login = os.environ.get("IIKO_SERVER_LOGIN", None)  # Replace with your login
        self.password = os.environ.get("IIKO_SERVER_PASSWORD", None)  # Replace with your password
        self.password_hash = hashlib.sha1(self.password.encode()).hexdigest()
        
        # Create configuration
        self.config = Configuration(host=self.server_url, debug=True)
        
        # Create API client with context manager support
        self.client = ApiClient(configuration=self.config)
        self.session_api = SessionManagementApi(api_client=self.client)
        await self.session_api.auth_post(login=self.login, var_pass=self.password_hash)
        self.api = ReplicationsApi(api_client=self.client)

        self.test_department_id = "65430fca-3116-f1b6-0197-5488678d0012"
        self.test_department_name = "Мой ресторан"

    async def asyncTearDown(self) -> None:
        """Очистка после каждого теста"""
        # Make sure to properly close all connections
        try:
            await self.session_api.logout_post()
        except Exception as e:
            print(f"Warning: logout failed: {e}")
        
        # Ensure client is closed properly
        await self.client.close()
        
        # Give event loop time to cleanup resources
        await asyncio.sleep(0.1)

    async def test_replication_server_type_get(self) -> None:
        """Тест получения типа сервера
        
        Тестирует получение типа сервера репликации
        """
        try:
            result = await self.api.replication_server_type_get()
            self.assertIsNotNone(result)
            self.assertIn(result, [
                ServerTypeEnum.CHAIN,
                ServerTypeEnum.REPLICATED_RMS,
                ServerTypeEnum.STANDALONE_RMS
            ])
            
            print(f"Server type: {result}")
            
        except Exception as e:
            self.fail(f"Server type test failed with error: {str(e)}")

    async def test_replication_statuses_get(self) -> None:
        """Тест получения статусов репликаций
        
        Тестирует получение списка статусов репликаций (работает только для CHAIN)
        """
        try:
            # Сначала проверим тип сервера
            #server_type = await self.api.replication_server_type_get()
            
            #if server_type != ServerTypeEnum.CHAIN:
            #    print(f"Skipping replication statuses test - server type is {server_type}, not CHAIN")
            #    return
            
            result = await self.api.replication_statuses_get()
            
            self.assertIsNotNone(result)
            self.assertIsInstance(result.replication_status_dtoes, list)
            
            print(f"Retrieved {len(result.replication_status_dtoes)} replication statuses")
            
                         # Проверяем структуру статусов репликации
            for status in result.replication_status_dtoes:
                self.assertIsInstance(status, ReplicationStatusDto)
                # departmentId может быть None для некоторых статусов
                if status.department_id is not None:
                    self.assertIsInstance(status.department_id, str)
                if status.department_name is not None:
                    self.assertIsInstance(status.department_name, str)
                if status.last_receive_date is not None:
                    self.assertIsInstance(status.last_receive_date, datetime)
                if status.last_send_date is not None:
                    self.assertIsInstance(status.last_send_date, datetime)
                if status.status is not None:
                    self.assertIsInstance(status.status, str)
                    
        except Exception as e:
            # Если это RMS сервер, ошибка ожидаема
            if "РМС" in str(e) or "RMS" in str(e):
                print(f"Expected error for RMS server: {str(e)}")
            else:
                self.fail(f"Replication statuses test failed with error: {str(e)}")

    async def test_replication_by_department_id_status_get(self) -> None:
        """Тест получения статуса репликации конкретного ТП
        
        Тестирует получение статуса репликации для конкретного департамента
        """
        try:
            # Сначала проверим тип сервера
            server_type = await self.api.replication_server_type_get()
            
            if server_type != ServerTypeEnum.CHAIN:
                print(f"Skipping department replication status test - server type is {server_type}, not CHAIN")
                return
            
            # Используем тестовый ID департамента
            result = await self.api.replication_by_department_id_department_id_status_get(
                department_id=self.test_department_id
            )
            
            self.assertIsNotNone(result)
            self.assertIsInstance(result, ReplicationStatusDto)
            
                         # Проверяем структуру статуса репликации
            if result.department_id is not None:
                self.assertEqual(result.department_id, self.test_department_id)
            if result.department_name is not None:
                self.assertIsInstance(result.department_name, str)
            if result.last_receive_date is not None:
                self.assertIsInstance(result.last_receive_date, datetime)
            if result.last_send_date is not None:
                self.assertIsInstance(result.last_send_date, datetime)
            if result.status is not None:
                self.assertIsInstance(result.status, str)
            
            print(f"Retrieved replication status for department: {self.test_department_id}")
            
        except Exception as e:
            # Если это RMS сервер или департамент не найден, ошибка ожидаема
            if "РМС" in str(e) or "RMS" in str(e) or "404" in str(e) or "не найден" in str(e):
                print(f"Expected error for RMS server or department not found: {str(e)}")
            else:
                self.fail(f"Department replication status test failed with error: {str(e)}")

    

if __name__ == '__main__':
    unittest.main() 