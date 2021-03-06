import pytest
import allure
from copy import deepcopy
from source.helpers.work_with_api import API
from source.helpers.work_with_fields import WorkCharacters
from source.data.data_expected_bodies import DATA_FOR_POST_CHARACTER_BY_BODY, DATA_CHANGED_NAME_FOR_PUT, \
    MIN_LENGTH_FIELD, WRONG_ORDER_OF_FIELDS, WRONG_ORDER_OF_FIELDS_EXPECTED, MISSING_REQUIRED_FIELD, \
    DATA_STANDARD_CHARACTER, POST_ONLY_REQUIRED_NAME
from source.data.data_expected_responses import RESPONSE_NEEDED_AUTHORIZATION, RESPONSE_SLICE_LOGIN, \
    RESPONSE_MISSING_REQUIRED_FIELD, RESPONSE_FIELD_LENGTH_ERROR, RESPONSE_INVALID_INPUT, \
    RESPONSE_NO_SUCH_NAME_CHARACTER, RESPONSE_CHARACTER_CREATED_ALREADY
from source.data.data_headers import HEADERS
from source.data.schema import CHARACTER_SCHEMA, ERROR_SCHEMA, RESULT_SCHEMA


@allure.title('Тестирование REST API')
@allure.link('https://github.com/Olexasha/test_ticket', name='GitHub')
@allure.link('http://rest.test.ivi.ru/v2/', name='Quest_Ticket')
class TestAPI(object):
    """
    Class to run tests by pytest
    """

    @allure.feature('Тестирование API')
    @allure.story('Стандартные HTTP методы')
    @pytest.mark.test_http_functional
    @pytest.mark.parametrize('data', DATA_FOR_POST_CHARACTER_BY_BODY)
    def test_get_character_by_name(self, data, login_auth, password_auth, create_several_characters,
                                   delete_several_characters):
        """
        Tests GET objects three times
        :param data: payload
        :param create_several_characters: setup fixture
        :param delete_several_characters: teardown fixture
        """
        response = API().get_character_by_name(raw_character_name=data["name"],
                                               login=login_auth, password=password_auth)
        assert response.compare_status_code(200)
        try:
            assert WorkCharacters.validate_fields(response.return_body(), CHARACTER_SCHEMA)
            assert response.compare_body({"result": data})
        except AssertionError as err:
            allure.attach(body=err, name='stderr', attachment_type=allure.attachment_type.TEXT)
            pytest.fail(err)

    @allure.feature('Тестирование API')
    @allure.story('Стандартные HTTP методы')
    @pytest.mark.test_http_functional
    @pytest.mark.parametrize('data', DATA_FOR_POST_CHARACTER_BY_BODY)
    def test_create_character(self, data, login_auth, password_auth, delete_several_characters):
        """
        Tests POST objects three times
        :param data: payload
        :param delete_several_characters: teardown fixture
        """
        response = API().post_character_by_body(json=data, login=login_auth, password=password_auth)
        assert response.compare_status_code(200)
        assert response.compare_body({"result": data})
        response = API().get_character_by_name(raw_character_name=data["name"], login=login_auth,
                                               password=password_auth)
        assert response.compare_status_code(200)
        try:
            assert WorkCharacters.validate_fields(response.return_body(), CHARACTER_SCHEMA)
            assert response.compare_body({"result": data})
        except AssertionError as err:
            allure.attach(body=err, name='stderr', attachment_type=allure.attachment_type.TEXT)
            pytest.fail(err)

    @allure.feature('Тестирование API')
    @allure.story('Стандартные HTTP методы')
    @pytest.mark.test_http_functional
    @pytest.mark.parametrize('data', DATA_FOR_POST_CHARACTER_BY_BODY)
    def test_delete_character_by_name(self, data, login_auth, password_auth, create_several_characters):
        """
        Tests DELETE objects three times
        :param data: payload
        :param create_several_characters: setup fixture
        """
        response = API().delete_character(raw_character_name=data["name"], login=login_auth, password=password_auth)
        deleted_hero = {"result": "Hero {0} is deleted".format(data["name"])}
        assert response.compare_status_code(200)
        try:
            assert WorkCharacters.validate_fields(response.return_body(), RESULT_SCHEMA)
            assert response.compare_body(deleted_hero)
        except AssertionError as err:
            allure.attach(body=err, name='stderr', attachment_type=allure.attachment_type.TEXT)
            pytest.fail(err)

    @allure.feature('Тестирование API')
    @allure.story('Стандартные HTTP методы')
    @pytest.mark.test_objects_api
    def test_headers_field(self, login_auth, password_auth):
        """
        Check headers fields by GET method
        """
        response = API().head_characters_page(login=login_auth, password=password_auth)
        assert response.compare_status_code(200)
        headers = response.return_headers()
        for key in headers.keys():
            match key:
                case "Server":
                    assert headers[key] == "nginx"
                case "Date":
                    assert headers[key] != '' and headers[key] != ' '
                case "Content-Type":
                    assert headers[key] == HEADERS["Content-Type"]
                case "Content-Length":
                    assert int(headers[key]) > 0
                case "Connection":
                    assert headers[key] == HEADERS["Connection"]

    @allure.feature('Тестирование API')
    @allure.step('Тест изменения поля существующего персонажа')
    @pytest.mark.test_http_functional
    @pytest.mark.parametrize('data', DATA_CHANGED_NAME_FOR_PUT)
    def test_update_character_identity_by_name(self, data, login_auth, password_auth, create_n_del_character):
        """
        Test PUT object
        :param data: payload
        :param create_n_del_character_for_put: setup and teardown fixture
        """
        response = API().put_character_by_name(json=data["result"],
                                               login=login_auth, password=password_auth)
        assert response.compare_status_code(200)
        try:
            assert response.compare_body(data)
        except AssertionError as err:
            allure.attach(body=err, name='stderr', attachment_type=allure.attachment_type.TEXT)
            pytest.fail(err)
        response = API().get_character_by_name(raw_character_name=data["result"]["name"],
                                               login=login_auth, password=password_auth)
        assert response.compare_status_code(200)
        try:
            assert WorkCharacters.validate_fields(response.return_body(), CHARACTER_SCHEMA)
            assert response.compare_body(data)
        except AssertionError as err:
            allure.attach(body=err, name='stderr', attachment_type=allure.attachment_type.TEXT)
            pytest.fail(err)

    @allure.feature('Тестирование API')
    @allure.story('Работа с со всеми экземплярами персонажей')
    @allure.step('Тест получения всех экземпляров персонажей')
    @pytest.mark.test_http_functional
    def test_get_all_characters(self, login_auth, password_auth, delete_3_characters_same_time):
        """
        Tests GET all objects. The status is checked before the creation of 3 characters and after
        :param create_3_characters: setup and teardown fixture
        """
        response = API().get_all_characters(login=login_auth, password=password_auth)
        assert response.compare_status_code(200)
        characters_before = response.count_all_characters()
        characters_after = WorkCharacters().count_after_create_chars(login=login_auth, password=password_auth)
        try:
            assert characters_before + 3 == characters_after
            assert WorkCharacters.validate_fields(response.return_body(), CHARACTER_SCHEMA)
        except AssertionError as err:
            allure.attach(body=err, name='stderr', attachment_type=allure.attachment_type.TEXT)
            pytest.fail(err)

    @allure.feature('Тестирование API')
    @allure.story('Работа с со всеми экземплярами персонажей')
    @allure.step('Тест на поиск одинаковых экземпляров персонажей')
    @pytest.mark.test_objects_api
    def test_get_all_duplicate_chars(self, login_auth, password_auth):
        """
        Tests for the presence of duplicate characters
        """
        response = API().get_all_characters(login=login_auth, password=password_auth)
        assert response.compare_status_code(200)
        try:
            assert WorkCharacters().find_duplicate_characters(response.return_body())
            assert WorkCharacters.validate_fields(response.return_body(), CHARACTER_SCHEMA)
        except AssertionError as err:
            allure.attach(body=err, name='stderr', attachment_type=allure.attachment_type.TEXT)
            pytest.fail(err)

    @allure.feature('Тестирование API')
    @allure.story('Коды ошибок')
    @pytest.mark.test_negative_cases
    def test_wrong_authorization(self, login_auth, password_auth):
        """
        Tests wrong authorization data in advance
        """
        response = API().get_all_characters(login=login_auth, password='dc_better_than_marvel')
        assert response.compare_status_code(401)
        assert WorkCharacters.validate_fields(response.return_body(), ERROR_SCHEMA)
        assert response.compare_body(RESPONSE_NEEDED_AUTHORIZATION)

    @allure.feature('Тестирование API')
    @allure.story('Коды ошибок')
    @pytest.mark.test_negative_cases
    def test_wrong_url_resource(self, login_auth, password_auth):
        """
        Tests API answers by getting wrong url resource
        """
        response = API().get_wrong_url_resource(login=login_auth, password=password_auth)
        assert response.compare_status_code(404)

    @allure.feature('Тестирование API')
    @allure.story('Коды ошибок')
    @pytest.mark.test_negative_cases
    def test_empty_login(self, login_auth, password_auth):
        """
        Tests wrong authorization by empty field
        """
        response = API().get_all_characters(login='', password=password_auth)
        assert response.compare_status_code(500)
        assert response.compare_raw_text(RESPONSE_SLICE_LOGIN)

    @allure.feature('Тестирование API')
    @allure.story('Коды ошибок')
    @pytest.mark.test_negative_cases
    def test_wrong_order_of_field(self, login_auth, password_auth, double_delete_character):
        """
        Tests POST method with wrong fields order
        :param double_delete_character: setup and teardown fixture
        """
        response = API().post_character_by_body(json=WRONG_ORDER_OF_FIELDS["result"],
                                                login=login_auth, password=password_auth)
        assert response.compare_status_code(200)
        try:
            assert WorkCharacters.validate_fields(response.return_body(), CHARACTER_SCHEMA)
            assert response.compare_body(WRONG_ORDER_OF_FIELDS_EXPECTED)
        except AssertionError as err:
            allure.attach(body=err, name='stderr', attachment_type=allure.attachment_type.TEXT)
            pytest.fail(err)

    @allure.feature('Тестирование API')
    @allure.story('Коды ошибок')
    @pytest.mark.test_negative_cases
    def test_delete_deleted_char(self, login_auth, password_auth):
        """
        Tests the correctness of the return body when DELETE a character 'Anyone' that does not exist
        """
        response = API().delete_character(raw_character_name="Anyone", login=login_auth, password=password_auth)
        assert response.compare_status_code(400)
        assert WorkCharacters.validate_fields(response.return_body(), ERROR_SCHEMA)
        assert response.compare_body(RESPONSE_NO_SUCH_NAME_CHARACTER)

    @allure.feature('Тестирование API')
    @allure.story('Коды ошибок')
    @pytest.mark.test_negative_cases
    def test_create_existing_char(self, login_auth, password_auth, create_n_del_character):
        """
        Tests the correctness of the return body when POST an existing 'Spider-Man' character
        :param create_n_del_character: setup and teardown fixture
        """
        response = API().post_character_by_body(json=DATA_FOR_POST_CHARACTER_BY_BODY[1], login=login_auth,
                                                password=password_auth)
        assert response.compare_status_code(400)
        assert WorkCharacters.validate_fields(response.return_body(), ERROR_SCHEMA)
        assert response.compare_body(RESPONSE_CHARACTER_CREATED_ALREADY)

    @allure.feature('Тестирование API')
    @allure.story('Коды ошибок')
    @allure.step('Тест получения несуществующего экземпляра персонажа')
    @pytest.mark.test_negative_cases
    def test_get_not_existing_char(self, login_auth, password_auth):
        """
        Tests the correctness of the body return when GET a non-existent 'Anyone' character
        """
        response = API().get_character_by_name(raw_character_name="Anyone",
                                               login=login_auth, password=password_auth)
        assert response.compare_status_code(400)
        assert WorkCharacters.validate_fields(response.return_body(), ERROR_SCHEMA)
        assert response.compare_body(RESPONSE_NO_SUCH_NAME_CHARACTER)

    @allure.feature('Тестирование API')
    @allure.story('Коды ошибок')
    @allure.step('Тест ввода некорректных данных')
    @pytest.mark.test_objects_api
    def test_post_wrong_input(self, login_auth, password_auth):
        """
        Tests POST wrong input data
        """
        data = deepcopy(MIN_LENGTH_FIELD["result"])
        payload = data.pop("name")
        response = API().post_character_by_body(json=payload, login=login_auth,
                                                password=password_auth)
        assert response.compare_status_code(400)
        assert WorkCharacters.validate_fields(response.return_body(), ERROR_SCHEMA)
        assert response.compare_body(RESPONSE_INVALID_INPUT)

    @allure.feature('Тестирование API')
    @allure.story('Проверки полей')
    @pytest.mark.test_objects_api
    def test_post_only_required_field(self, login_auth, password_auth):
        """
        Tests POST only required field 'name'
        """
        response = API().post_character_by_body(json=POST_ONLY_REQUIRED_NAME["result"], login=login_auth,
                                                password=password_auth)
        assert response.compare_status_code(200)
        try:
            assert WorkCharacters.validate_fields(response.return_body(), CHARACTER_SCHEMA)
            assert response.compare_body(POST_ONLY_REQUIRED_NAME)
        except AssertionError as err:
            allure.attach(body=err, name='stderr', attachment_type=allure.attachment_type.TEXT)
            pytest.fail(err)

    @allure.feature('Тестирование API')
    @allure.story('Проверки полей')
    @pytest.mark.test_objects_api
    def test_post_missing_required_field(self, login_auth, password_auth):
        """
        Tests the empty value of required field 'name'
        """
        response = API().post_character_by_body(json=MISSING_REQUIRED_FIELD, login=login_auth,
                                                password=password_auth)
        assert response.compare_status_code(400)
        assert WorkCharacters.validate_fields(response.return_body(), ERROR_SCHEMA)
        assert response.compare_body(RESPONSE_MISSING_REQUIRED_FIELD)

    @allure.feature('Тестирование API')
    @allure.story('Проверки полей')
    @pytest.mark.test_objects_api
    def test_post_min_field_positive(self, login_auth, password_auth, reset_database_after):
        """
        Tests the minimum symbols length of the field
        """
        data = deepcopy(MIN_LENGTH_FIELD)
        payload = WorkCharacters().make_field_symbols(data["result"], 1)
        response = API().post_character_by_body(json=payload, login=login_auth, password=password_auth)
        assert response.compare_status_code(200)
        try:
            assert WorkCharacters.validate_fields(response.return_body(), CHARACTER_SCHEMA)
            assert response.compare_body({"result": payload})
        except AssertionError as err:
            allure.attach(body=err, name='stderr', attachment_type=allure.attachment_type.TEXT)
            pytest.fail(err)

    @allure.feature('Тестирование API')
    @allure.story('Проверки полей')
    @pytest.mark.test_objects_api
    def test_post_max_field_positive(self, login_auth, password_auth, reset_database_after):
        """
        Tests the maximum symbols length of the field
        """
        data = deepcopy(MIN_LENGTH_FIELD)
        payload = WorkCharacters().make_field_symbols(data["result"], 350)
        response = API().post_character_by_body(json=payload, login=login_auth, password=password_auth)
        assert response.compare_status_code(200)
        try:
            assert WorkCharacters.validate_fields(response.return_body(), CHARACTER_SCHEMA)
            assert response.compare_body({"result": payload})
        except AssertionError as err:
            allure.attach(body=err, name='stderr', attachment_type=allure.attachment_type.TEXT)
            pytest.fail(err)

    @allure.feature('Тестирование API')
    @allure.story('Проверки полей')
    @pytest.mark.test_negative_cases
    def test_post_min_field_negative(self, login_auth, password_auth, reset_database_after):
        """
        Tests the minimum symbols length of the field
        """
        data = deepcopy(MIN_LENGTH_FIELD)
        payload = WorkCharacters().make_field_symbols(data["result"], 0)
        response = API().post_character_by_body(json=payload, login=login_auth, password=password_auth)
        assert response.compare_status_code(400)
        assert response.compare_body(RESPONSE_FIELD_LENGTH_ERROR)

    @allure.feature('Тестирование API')
    @allure.story('Проверки полей')
    @pytest.mark.test_negative_cases
    def test_post_max_field_negative(self, login_auth, password_auth, reset_database_after):
        """
        Tests the maximum symbols length of the field
        """
        data = deepcopy(MIN_LENGTH_FIELD)
        payload = WorkCharacters().make_field_symbols(data["result"], 351)
        response = API().post_character_by_body(json=payload, login=login_auth, password=password_auth)
        assert response.compare_status_code(400)
        assert response.compare_body(RESPONSE_FIELD_LENGTH_ERROR)

    @allure.feature('Тестирование API')
    @allure.story('Проверки полей')
    @pytest.mark.test_http_functional
    @pytest.mark.parametrize('data', DATA_STANDARD_CHARACTER)
    def test_reset_database(self, data, login_auth, password_auth, create_character):
        """
        Tests the correctness of database reseting
        :param data: standart character
        :param create_character: setup fixture which creates standart character
        """
        response = API().delete_all_characters(login_auth, password_auth)
        assert response.compare_status_code(200)
        response = API().get_character_by_name(raw_character_name=data["result"]["name"],
                                               login=login_auth, password=password_auth)
        assert WorkCharacters.validate_fields(response.return_body(), ERROR_SCHEMA)
        assert response.compare_body(RESPONSE_NO_SUCH_NAME_CHARACTER)
