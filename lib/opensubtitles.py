# User-Agent registered with Opensubtitles.org (https://trac.opensubtitles.org/projects/opensubtitles/wiki/DevReadFirst)
UA = ''

import xmlrpclib, os, struct
import random
import logging

# A plug-in for xmlrpclib's default Transport class, as the default one isn't supported on GAE
import xmlrpc

class OpenSubtitles:
	# OS.org API server
	apiServer = 'http://api.opensubtitles.org/xml-rpc'
	token = None

	def __init__(self, uagent=None):
		self.proxy = xmlrpclib.ServerProxy(self.apiServer, xmlrpc.GAEXMLRPCTransport())
		self.userAgent = uagent or UA
		logging.info('Using UA: '+self.userAgent)

	def __del__(self):
		self.logout()

	def ping(self):
		return self.proxy.ServerInfo

	def login(self, username='', password='', language='en'):
		if self.token == None:
			response = self.proxy.LogIn(username, password, language, self.userAgent)
			if response['status'] == '200 OK':
				self.token = response['token']
				logging.info('Token: '+self.token)

	def logout(self):
		if self.token != None:
			self.proxy.LogOut(self.token)

	def _checkToken(self):
		if self.token is None:
			raise Exception, 'Token not initialized'

	def _returnDataIfNotEmpty(self, results):
		if results['data'] is not False:
			if results['data']:
				return results['data']
			logging.warning('No Data')
			return []

	# Filter results by matching the year-searched and year-returned
	def _filterByYear(self, lst, year):
		if lst is not False:
			if lst:
				return [x for x in lst if x['MovieYear'] == str(year)]
			return []

	def _getUnique(self, results):
		d = {}
		for result in results:
			d[result['MovieReleaseName'].strip()] = result
		return d.values()

	def searchMoviesWithImdbId(self, imdbid, year):
		self._checkToken()
		results = self.proxy.SearchSubtitles(self.token, [{'imdbid': imdbid, 'sublanguageid': 'eng'}], {'limit':12})
		return self._filterByYear(lst=self._getUnique(self._returnDataIfNotEmpty(results)), year=year)

	def searchMoviesWithQuery(self, name, year):
		self._checkToken()
		results = self.proxy.SearchSubtitles(self.token, [{'query': name, 'sublanguageid': 'eng'}], {'limit':12})
		return self._filterByYear(lst=self._getUnique(self._returnDataIfNotEmpty(results)), year=year)

	def searchTVWithImdbId(self, imdbid, season, episode):
		self._checkToken()
		results = self.proxy.SearchSubtitles(self.token, [{'imdbid': imdbid, 'season': season, 'episode': episode, 'sublanguageid': 'eng'}], {'limit':12})
		return self._getUnique(self._returnDataIfNotEmpty(results))

	def searchTVWithQuery(self, name, season, episode):
		self._checkToken()
		results = self.proxy.SearchSubtitles(self.token, [{'query': name, 'season': season, 'episode': episode, 'sublanguageid': 'eng'}], {'limit':12})
		return self._getUnique(self._returnDataIfNotEmpty(results))