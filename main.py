import webapp2
from google.appengine.ext import db
from google.appengine.ext import vendor
from datetime import datetime
import logging
import re

# Instruct GAE to add the ./lib folder to LD_LIBRARY_PATH
vendor.add('lib')

import praw
import opensubtitles
import PTN
import hashlib

# OpenSubtitles.org Credentials - Without these, you will have a 200 per day download limit
OSORG_USERNAME = ''
OSORG_PASSWORD = ''

# PRAW Settings - An application must be registered on Reddit to get the client_id and client_secret details. Redirect URI set below must match the one entered during the application registration
CLIENT_ID = ''
CLIENT_SECRET = ''
REFRESH_TOKEN = ''
r = praw.Reddit('SubZorro by u/indigo6alpha', disable_update_check=True)
r.config._ssl_url = None
r.set_oauth_app_info(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, redirect_uri='http://127.0.0.1:65010/authorize_callback');
r.refresh_access_information(REFRESH_TOKEN);

# GAE Datastore Entity Definition
class LookEntry(db.Model):
	content = db.ListProperty(str,indexed=False,default=[])
	date = db.DateTimeProperty(auto_now_add=True)

# GAE Datastore get ancestor key
def lookdb_key():
	return db.Key.from_path('LookDB', 'looker')

# Filter the list of subtitles by name
def filterByName(lst, name):
	for lstitem in lst:
		if all(x in lstitem['MovieReleaseName'] for x in name.split(' ')):
			yield lstitem

# Request Handler for '/'
class MainPage(webapp2.RequestHandler):
	def get(self):
		self.response.headers['Content-Type'] = 'text/plain'
		u = r.get_me()
		self.response.write('Hello! You have '+str(u.link_karma)+' Link Karma')

# Request Handler for '/scan'
class ScanPage(webapp2.RequestHandler):
	def get(self):
		self.response.headers['Content-type'] = 'application/json'
		self.response.out.write("> Initializing")
		osdb = opensubtitles.OpenSubtitles()
		osdb.login(username=OSORG_USERNAME, password=OSORG_PASSWORD)
		l = self.get_entity()
		logging.info(l.content)
		subreddit = r.get_subreddit('SubZorro')
		try:
			submissions = subreddit.get_new(limit=20)
		except praw.errors.HTTPException as h:
			self.response.out.write("> HTTP ERROR\n")

		# Comment Template
		ctitle = ""
		endmsg = """^This ^list ^of ^subtitles ^are ^taken ^from [^opensubtitles.org](http://www.opensubtitles.org) ^|"""
		shelp = " ^For ^feedback ^or ^suggestions ^contact [^/u/indigo6alpha](http://www.reddit.com/message/compose/?to=indigo6alpha)"
		endmsg = endmsg + shelp
		br = "\n\n---\n\n"

		for submission in submissions:
			visited = False
			summ = ""

			# Check all entities in the Datastore for this submission ID
			if(self.check_id(subid=submission.id)):
				try:
					
					_tag = re.search("""\[(Movie|MOVIE|movie|TV|tv|Tv)\]""", submission.title)

					l.content.append(submission.id)
					l.put()

					# Check if the submission has a movie or a tv tag
					if _tag is None or _tag.group(1).lower() not in ['movie','tv']:
						logging.info("No relevant tag found")
						continue

					comments_tree = submission.comments

					for comment in comments_tree:
						if str(comment.author) == 'SubZorro':
							visited = True

					if(visited == True):
						continue

					logging.info(submission.title)

					attrs = PTN.parse(re.sub("""\[(.*?)\]""","", submission.title).strip())
					subs = {}
					try:
						if(attrs.has_key('season') and attrs.has_key('episode')):
							ctitle = "#####Subtitles for this episode: "
							subs = filterByName(osdb.searchTVWithQuery(name=attrs['title'],season=str(attrs['season']),episode=str(attrs['episode'])), attrs['title'])
						elif(attrs.has_key('year')):
							ctitle = "#####Subtitles for this movie: "
							subs = filterByName(osdb.searchMoviesWithQuery(name=attrs['title'], year=str(attrs['year'])), attrs['title'])
						else:
							self.response.out.write("> Skipping "+submission.id+"\n")
							continue

					except Exception as ex:
						logging.warning("Exception: "+str(ex))
						continue

					if subs != [] and subs != None:
						try:
							for sub in subs:
								shash = hashlib.md5(sub['IDSubtitle']).hexdigest()[:8]
								summ += "> - **"+sub['MovieReleaseName'].strip()+"** - `"+sub['SubSumCD']+" CD` - [Download Subtitle](http://dl.opensubtitles.org/en/download/vrf-"+shash+"/sub/"+sub['IDSubtitle']+")\n\n"

							submission.add_comment(ctitle + br + summ.encode('ascii', 'ignore') + br + endmsg)
							self.response.out.write("> Posted subtitles for "+submission.id+"\n")
							continue

						except Exception as e:
							logging.warning("Subtitles Error: "+str(e))
							continue
					else:
						self.response.out.write("> No subtitles found for: "+submission.id+"\n")
						continue

				except Exception as e:
					logging.warning("Submission Error: "+str(e))
					continue

		self.response.write("> Done looping through submissions")

	def get_entity(self):
		entries = db.GqlQuery("SELECT * FROM LookEntry WHERE ANCESTOR IS :1 ORDER BY date DESC LIMIT 10", lookdb_key())
		d = str(datetime.now().date())
		found = False

		for entr in entries:
			dn = str(entr.date.date())
			if(dn == d):
				found = True
				return entr
			else:
				continue

		if(found == False):
			lookentr = LookEntry(parent=lookdb_key())
			lookentr.put()
			return lookentr

	# Returns True if there's no match, False if the ID is found is any of the ListProperty elements of the entities
	def check_id(self, subid):
		entries = db.GqlQuery("SELECT * FROM LookEntry WHERE ANCESTOR IS :1 ORDER BY date DESC", lookdb_key())

		for entr in entries:
			if subid in entr.content:
				return False

		return True

app = webapp2.WSGIApplication([
	('/', MainPage),
	('/scan', ScanPage),
], debug=True)
