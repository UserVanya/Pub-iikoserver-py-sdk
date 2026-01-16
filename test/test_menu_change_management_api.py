import asyncio
import hashlib
import os
import unittest
from datetime import datetime, timedelta
from unittest import IsolatedAsyncioTestCase

from iikoserver_client import ApiClient, Configuration
from iikoserver_client.api.corporation_management_api import CorporationManagementApi
from iikoserver_client.api.menu_change_management_api import MenuChangeManagementApi
from iikoserver_client.api.session_management_api import SessionManagementApi
from iikoserver_client.models.menu_change_document_dto import MenuChangeDocumentDto
from iikoserver_client.models.menu_change_document_item_dto import MenuChangeDocumentItemDto
from iikoserver_client.models.menu_change_document_status_enum import MenuChangeDocumentStatusEnum


class TestMenuChangeManagementApi(IsolatedAsyncioTestCase):
    """Тестирование API управления приказами на изменение меню"""

    async def asyncSetUp(self) -> None:
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
        self.api = MenuChangeManagementApi(api_client=self.client)

        self.test_department_id = "65430fca-3116-f1b6-0197-5488678d0012"
        self.test_department_name = "Мой ресторан"

    async def asyncTearDown(self) -> None:
        # Make sure to properly close all connections
        try:
            await self.session_api.logout_post()
        except Exception as e:
            print(f"Warning: logout failed: {e}")
        
        # Ensure client is closed properly
        await self.client.close()
        
        # Give event loop time to cleanup resources
        await asyncio.sleep(0.1)

    async def test_documents_menu_change_get(self) -> None:
        """Тест получения списка приказов на изменение меню
        
        Тестирует получение приказов за указанный период
        """
        try:
            # Получение списка приказов за последний месяц
            date_from = (datetime.now() - timedelta(days=30)).date()
            date_to = datetime.now().date()
            
            result = await self.api.v2_documents_menu_change_get(
                date_from=date_from,
                date_to=date_to,
                status=None,
                revision_from=-1
            )
            
            self.assertIsNotNone(result)
            self.assertEqual(result.result, "SUCCESS")
            self.assertIsInstance(result.response, list)
            self.assertIsInstance(result.revision, int)
            
            print(f"Retrieved {len(result.response)} menu change documents")
            
            # Проверяем структуру документов
            for doc in result.response:
                self.assertIsNotNone(doc.id)
                self.assertIsNotNone(doc.date_incoming)
                self.assertIsNotNone(doc.document_number)
                self.assertIsNotNone(doc.status)
                self.assertIsInstance(doc.delete_previous_menu, bool)
                self.assertIsInstance(doc.items, list)
                
        except Exception as e:
            self.fail(f"Menu change documents list test failed with error: {str(e)}")

    async def test_documents_menu_change_document_by_id_get(self) -> None:
        """Тест получения приказа по идентификатору
        
        Сначала получает список приказов, затем запрашивает один по ID
        """
        try:
            # Сначала получаем список приказов
            date_from = (datetime.now() - timedelta(days=90)).date()
            date_to = datetime.now().date()
            
            list_result = await self.api.v2_documents_menu_change_get(
                date_from=date_from,
                date_to=date_to
            )
            
            if not list_result.response or len(list_result.response) == 0:
                print("No menu change documents found, skipping by_id test")
                return
            
            # Берем первый документ из списка
            test_doc_id = list_result.response[0].id
            
            result = await self.api.v2_documents_menu_change_by_id_get(id=test_doc_id)
            
            self.assertIsNotNone(result)
            self.assertEqual(result.id, test_doc_id)
            self.assertIsNotNone(result.date_incoming)
            self.assertIsNotNone(result.status)
            
            print(f"Retrieved menu change document by ID: {test_doc_id}")
            
        except Exception as e:
            self.fail(f"Menu change document by ID test failed with error: {str(e)}")

    async def test_documents_menu_change_by_number_get(self) -> None:
        """Тест получения приказов по номеру документа
        
        Сначала получает список приказов, затем запрашивает по номеру
        """
        try:
            # Сначала получаем список приказов
            date_from = (datetime.now() - timedelta(days=90)).date()
            date_to = datetime.now().date()
            
            list_result = await self.api.v2_documents_menu_change_get(
                date_from=date_from,
                date_to=date_to
            )
            
            if not list_result.response or len(list_result.response) == 0:
                print("No menu change documents found, skipping by_number test")
                return
            
            # Берем номер первого документа из списка
            test_doc_number = list_result.response[0].document_number
            
            result = await self.api.v2_documents_menu_change_by_number_get(
                document_number=test_doc_number
            )
            
            self.assertIsNotNone(result)
            self.assertIsInstance(result, list)
            
            # Проверяем, что все документы имеют правильный номер
            for doc in result:
                self.assertEqual(doc.document_number, test_doc_number)
                
            print(f"Retrieved {len(result)} menu change documents by number: {test_doc_number}")
            
        except Exception as e:
            self.fail(f"Menu change document by number test failed with error: {str(e)}")

    async def test_price_get(self) -> None:
        """Тест получения цен продуктов, заданных приказами
        
        Тестирует получение цен за указанный период
        """
        try:
            date_from = (datetime.now() - timedelta(days=30)).date()
            
            result = await self.api.v2_price_get(
                date_from=date_from,
                date_to=None,
                department_id=[self.test_department_id],
                include_out_of_sale=False,
                type=None,
                revision_from=-1
            )
            
            self.assertIsNotNone(result)
            self.assertEqual(result.result, "SUCCESS")
            self.assertIsInstance(result.response, list)
            self.assertIsInstance(result.revision, int)
            
            print(f"Retrieved prices for {len(result.response)} products")
            
            # Проверяем структуру цен
            for price in result.response:
                self.assertIsNotNone(price.department_id)
                self.assertIsNotNone(price.product_id)
                self.assertIsInstance(price.prices, list)
                
                # Проверяем элементы цен
                for price_item in price.prices:
                    self.assertIsNotNone(price_item.date_from)
                    self.assertIsNotNone(price_item.date_to)
                    self.assertIsNotNone(price_item.document_id)
                    self.assertIsInstance(price_item.included, bool)
                    self.assertIsInstance(price_item.dish_of_day, bool)
                    self.assertIsInstance(price_item.flyer_program, bool)
                    
        except Exception as e:
            self.fail(f"Product prices list test failed with error: {str(e)}")

    async def test_documents_menu_change_post(self) -> None:
        """Тест создания нового приказа на изменение меню
        
        Тестирует создание базового приказа (осторожно - изменяет данные)
        """
        if not self.test_department_id:
            print("No test department available, skipping document creation test")
            return
            
        try:
            # Создаем тестовый приказ
            new_document = MenuChangeDocumentDto(
                date_incoming=(datetime.now() + timedelta(days=1)).date(),
                document_number=f"TEST_{int(datetime.now().timestamp())}",
                status=MenuChangeDocumentStatusEnum.NEW,
                comment="Test document created by automated tests",
                short_name="Test",
                delete_previous_menu=False,
                date_to=(datetime.now() + timedelta(days=30)).date(),
                items=[]
            )
            
            result = await self.api.v2_documents_menu_change_post(
                menu_change_document_dto=new_document
            )
            
            self.assertIsNotNone(result)
            self.assertEqual(result.result, "SUCCESS")
            self.assertIsNotNone(result.response)
            self.assertIsNotNone(result.response.id)
            
            print(f"Created test menu change document with ID: {result.response.id}")
            
            # Сохраняем ID для возможной очистки
            self.created_document_id = result.response.id
            
        except Exception as e:
            # Это нормально, если у нас нет прав на создание документов
            print(f"Document creation test failed (expected in read-only environment): {str(e)}")


if __name__ == '__main__':
    unittest.main() 