"""
Тесты для API управления быстрыми меню
"""
import asyncio
import hashlib
import os
import unittest
from datetime import datetime, timedelta
from unittest import IsolatedAsyncioTestCase

from iikoserver_client import ApiClient, Configuration
from iikoserver_client.api.fast_menu_management_api import FastMenuManagementApi
from iikoserver_client.api.session_management_api import SessionManagementApi
from iikoserver_client.api.nomenclature_management_api import NomenclatureManagementApi

from iikoserver_client.models.quick_menu_dto import QuickMenuDto
from iikoserver_client.models.quick_label_dto import QuickLabelDto
from iikoserver_client.models.quick_label_entity_type_enum import QuickLabelEntityTypeEnum
from iikoserver_client.models.quick_menu_filter_form_dto import QuickMenuFilterFormDto
from iikoserver_client.models.quick_menu_create_dto import QuickMenuCreateDto
from iikoserver_client.models.quick_menu_update_dto import QuickMenuUpdateDto
from iikoserver_client.models.quick_menu_delete_dto import QuickMenuDeleteDto
from iikoserver_client.models.quick_label_create_dto import QuickLabelCreateDto


class TestFastMenuManagementApi(IsolatedAsyncioTestCase):
    """Тестирование API управления быстрыми меню"""

    async def asyncSetUp(self) -> None:
        """Настройка перед каждым тестом"""
        # Read credentials from env variables or set them directly
        self.server_url = os.environ.get("IIKO_SERVER_URL", None)
        self.login = os.environ.get("IIKO_SERVER_LOGIN", None)
        self.password = os.environ.get("IIKO_SERVER_PASSWORD", None)
        self.password_hash = hashlib.sha1(self.password.encode()).hexdigest()
        
        # Create configuration
        self.config = Configuration(host=self.server_url, debug=True)
        
        # Create API client with context manager support
        self.client = ApiClient(configuration=self.config)
        self.session_api = SessionManagementApi(api_client=self.client)
        await self.session_api.auth_post(login=self.login, var_pass=self.password_hash)
        self.api = FastMenuManagementApi(api_client=self.client)
        self.nomenclature_api = NomenclatureManagementApi(api_client=self.client)
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

    async def test_entities_quick_labels_list_get(self) -> None:
        """Тест получения списка быстрых меню (GET)
        
        Тестирует получение всех быстрых меню
        """
        try:
            result = await self.api.v2_entities_quick_labels_list_get(
                include_deleted=False
            )
            
            self.assertIsNotNone(result)
            self.assertIsInstance(result, list)
            
            print(f"Retrieved {len(result)} quick menus")
            
            # Проверяем структуру быстрых меню
            for quick_menu in result:
                self.assertIsInstance(quick_menu, QuickMenuDto)
                self.assertIsNotNone(quick_menu.id)
                self.assertIsInstance(quick_menu.deleted, bool)
                self.assertIsInstance(quick_menu.depends_on_week_day, bool)
                self.assertIsNotNone(quick_menu.department_id)
                # section_id может быть None
                self.assertIsNotNone(quick_menu.page_names)
                self.assertEqual(len(quick_menu.page_names), 3)
                self.assertIsNotNone(quick_menu.labels)
                self.assertIsInstance(quick_menu.labels, list)
                
                # Проверяем структуру ячеек
                for label in quick_menu.labels:
                    self.assertIsInstance(label, QuickLabelDto)
                    # day может быть None
                    self.assertIsNotNone(label.page)
                    self.assertIn(label.page, [0, 1, 2])
                    self.assertIsNotNone(label.x)
                    self.assertIn(label.x, [0, 1, 2])
                    self.assertIsNotNone(label.y)
                    self.assertIn(label.y, [0, 1, 2, 3, 4, 5, 6, 7])
                    self.assertIsNotNone(label.entity_id)
                    self.assertIsNotNone(label.entity_type)
                    self.assertIn(label.entity_type, [
                        QuickLabelEntityTypeEnum.PRODUCT,
                        QuickLabelEntityTypeEnum.PRODUCT_GROUP
                    ])
                    
        except Exception as e:
            self.fail(f"Quick labels list GET test failed with error: {str(e)}")

    async def test_entities_quick_labels_list_post(self) -> None:
        """Тест получения списка быстрых меню (POST)
        
        Тестирует получение быстрых меню с фильтрацией через POST с form data
        """
        try:
            filter_form = QuickMenuFilterFormDto(
                include_deleted=False,
                department_id=[self.test_department_id]
            )

            result = await self.api.v2_entities_quick_labels_list_post(
                quick_menu_filter_form_dto=filter_form
            )
            
            self.assertIsNotNone(result)
            self.assertIsInstance(result, list)
            
            print(f"Retrieved {len(result)} quick menus with form filter")
            
            # Проверяем что все меню принадлежат нужному подразделению
            for quick_menu in result:
                self.assertEqual(quick_menu.department_id, self.test_department_id)
                
        except Exception as e:
            self.fail(f"Quick labels list POST test failed with error: {str(e)}")

    async def test_entities_quick_labels_save_post(self) -> None:
        """Тест создания быстрого меню"""
        try:
            # Получаем список продуктов через NomenclatureManagementApi
            products = await self.nomenclature_api.v2_entities_products_list_get(
                include_deleted=False,
            )

            test_product_id = None
            if products:
                test_product_id = products[0].id if hasattr(products[0], 'id') else products[0]['id']
            
            create_dto = QuickMenuCreateDto(
                depends_on_week_day=False,
                department_id=self.test_department_id,
                section_id=None,
                page_names=["Test1", "Test2", "Test3"],
                labels=[
                    QuickLabelCreateDto(
                        day=None,
                        page=0,
                        x=0,
                        y=0,
                        entity_id=test_product_id
                    )
                ]
            )
            
            created_menu = await self.api.v2_entities_quick_labels_save_post(
                quick_menu_create_dto=create_dto
            )
            
            self.assertIsNotNone(created_menu)
            self.assertIsInstance(created_menu.response, QuickMenuDto)
            self.assertEqual(created_menu.response.department_id, self.test_department_id)
            self.assertEqual(created_menu.response.page_names, ["Test1", "Test2", "Test3"])
            self.assertFalse(created_menu.response.deleted)
            
            print(f"Created quick menu with ID: {created_menu.response.id}")
            
        except Exception as e:
            self.fail(f"Quick menu save test failed with error: {str(e)}")

    async def test_entities_quick_labels_update_post(self) -> None:
        """Тест обновления быстрого меню"""
        try:
            products = await self.nomenclature_api.v2_entities_products_list_get(
                include_deleted=False,
            )

            test_product_id = None
            if products:
                test_product_id = products[1].id if hasattr(products[1], 'id') else products[0]['id']
            
            menu_list = await self.api.v2_entities_quick_labels_list_get(
                include_deleted=False
            )
            if menu_list:
                created_menu = menu_list[0]
            else:
                raise Exception("No quick menu found")
            # Обновляем меню
            update_dto = QuickMenuUpdateDto(
                id=created_menu.id,
                depends_on_week_day=True,  # Изменяем на True
                department_id=self.test_department_id,
                section_id=None,
                page_names=["Updated1", "Updated2", "Updated3"],
                labels=[
                    QuickLabelCreateDto(
                        day=1,  # Понедельник
                        page=1,
                        x=1,
                        y=1,
                        entity_id=test_product_id
                    )
                ]
            )
            
            updated_menu = await self.api.v2_entities_quick_labels_update_post(
                quick_menu_update_dto=update_dto
            )
            
            self.assertIsNotNone(updated_menu)
            self.assertEqual(updated_menu.response.id, created_menu.id)
            self.assertEqual(updated_menu.response.page_names, ["Updated1", "Updated2", "Updated3"])
            self.assertTrue(updated_menu.response.depends_on_week_day)
            self.assertEqual(len(updated_menu.response.labels), 1)
            self.assertEqual(updated_menu.response.labels[0].day, 1)
            self.assertEqual(updated_menu.response.labels[0].page, 1)
            
            print(f"Updated quick menu with ID: {updated_menu.response.id}")
            
        except Exception as e:
            self.fail(f"Quick menu update test failed with error: {str(e)}")

    async def test_entities_quick_labels_delete_post(self) -> None:
        """Тест удаления быстрого меню"""
        try:
            menu_list = await self.api.v2_entities_quick_labels_list_get(
                include_deleted=False
            )
            if menu_list:
                created_menu = menu_list[0]
            else:
                raise Exception("No quick menu found")
            deleted_menu = await self.api.v2_entities_quick_labels_delete_post(
                quick_menu_delete_dto=QuickMenuDeleteDto(id=created_menu.id)
            )
            
            self.assertIsNotNone(deleted_menu)
            self.assertEqual(deleted_menu.response.id, created_menu.id)
            self.assertTrue(deleted_menu.response.deleted)
            
            print(f"Deleted quick menu with ID: {deleted_menu.response.id}")
            
            # Проверяем что удаленное меню появляется при запросе с includeDeleted=True
            all_menus = await self.api.v2_entities_quick_labels_list_get(
                include_deleted=True,
                id=[deleted_menu.response.id]
            )
            
            self.assertIsNotNone(all_menus)
            self.assertEqual(len(all_menus), 1)
            self.assertTrue(all_menus[0].deleted)
            
        except Exception as e:
            self.fail(f"Quick menu delete test failed with error: {str(e)}")

    

if __name__ == '__main__':
    unittest.main() 