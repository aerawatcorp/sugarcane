import os
import json

from typing import Dict, Literal
from datetime import datetime
from django.core.validators import URLValidator
from django.utils import timezone
from urllib import parse

from .exceptions import CaneException


def build_url(url: str, relative_url: str = "", query_params: dict = {}) -> str:
	"""Build absolute url
	Args:
		url: URL path
		relative_url: Relative URL path
		query_params (dict): Query params for the url. Defaults to {}
	"""
	UrlValidator()(url)
	
	parsed_url = parse.urlparse(url)
	parsed_query = parse.parse_qs(parsed_url.query)
	query_params.update(parsed_query)
	url = parsed_url.scheme + "://" + parsed_url.netloc
	
	absoulte_url = parse.urljoin(url, relative_url)
	if query_params:
		absoulte_url = absoulte_url + "?" + parse.urlencode(query_params, doseq=True)
	return absoulte_url


def get_local_time() -> datetime:
	return timezone.now().astimezone(timezone.get_current_timezone())


class FileHandler:
	def read(file_path: str) -> str:
		if not os.path.exists(file_path):
			raise CaneException("File path does not exist")
		
		with open(file_path, "r") as file:
			return json.loads(file.read())

	def write(file_path: str, data: dict, mode: Literal['w', 'a'] = "w") -> bool:
		directory = os.path.dirname(file_path)
		if not os.path.exists(directory):
			os.makedirs(directory)
		
		with open(file_path, mode) as file:
			json.dump(data, file)

		return True
