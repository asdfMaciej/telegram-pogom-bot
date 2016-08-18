# -*- coding: utf-8 -*-
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium.common.exceptions import TimeoutException
from telegram.ext import Updater, CommandHandler, Job
import thread
import datetime
import traceback
import googlemaps


class MainHandler:
	def __init__(self, telegram_api_key, maps_api_key):
		self.api_key = telegram_api_key
		self.maps_api_key = maps_api_key
		self.pokes = []
		self.wanted_pokemon = []
		self.fajne_poki = {}
		self.fajne_poki_l = ['rzadkie', 'ewolucja']
		self.gmaps = googlemaps.Client(key=self.maps_api_key)
		self.timers = dict()

		self.fajne_poki['rzadkie'] = [
			'Dratini', 'Mr. Mime', 'Weezing', 'Lickitung',
			'Hitmonchan', 'Hitmonlee', 'Gengar', 'Cloyster',
			'Machoke', 'Poliwrath', 'Poliwhirl', 'Growlithe',
			'Mankey', 'Diglett', 'Wigglytuff', 'Clefairy',
			'Kabuto', 'Porygon', 'Cubone', 'Vileplume',
			'Vulpix', 'Ponyta', 'Rhyhorn', 'Gloom', 'Ekans',
			'Seaking', 'Geodude', 'Bulbasaur', 'Squirtle',
			'Charmander', 'Pikachu', 'Electabuzz', 'Scyther',
			'Snorlax', 'Haunter', 'Wartortle', 'Blastoise',
			'Slowpoke', 'Psyduck', 'Meowth', 'Koffing',
			'Hypno', 'Magnemite', 'Exeggcute', 'Voltorb',
			'Jynx', 'Ponyta', 'Ivysaur', 'Venusaur',
			'Charmeleon', 'Charizard', 'Jolteon', 'Flareon',
			'Vaporeon', 'Aerodactyl', 'Lapras', 'Arbok',
			'Raichu', 'Sandshrew', 'Sandslash', 'Nidoqueen',
			'Nidoking', 'Clefable', 'Ninetales', 'Dugtrio',
			'Persian', 'Golduck', 'Primeape', 'Arcanine',
			'Kadabra', 'Alakazam', 'Machamp', 'Victreebel',
			'Tentacruel', 'Graveler', 'Golem', 'Rapidash',
			'Kabutops', 'Slowbro', 'Magneton', 'Dewgong',
			'Muk', 'Onix', 'Electrode', 'Exeggutor',
			'Marowak', 'Rhydon', 'Chansey', 'Tangela',
			'Starmie', 'Magmar', 'Pinsir'
		]
		self.fajne_poki['ewolucja'] = [
			'Drowzee', 'Eevee', 'Zubat', 'Paras',
			'Oddish', 'Bellsprout', 'Shellder',
			'Staryu', 'Tentacool'
		]

	def generate_output(self, line):
		params = line.split('|||')
		pokemon = params[0]
		latitude = params[1]
		longitude = params[2]
		despawn_epoch = params[3]

		if pokemon not in self.wanted_pokemon:
			return None

		geocode = self.gmaps.reverse_geocode((float(latitude), float(longitude)))
		street = geocode[0]['address_components'][1]['long_name']
		streetno = geocode[0]['address_components'][0]['long_name']
		maps_text = "https://www.google.pl/maps/search/"+latitude
		maps_text += ","+longitude+"/"

		

		try:
			despawn_t = float(despawn_epoch.split('.')[0])
			time_text = str(datetime.datetime.now()+datetime.timedelta(0, despawn_t))
			time_text = time_text.split('.')[0].split(' ')[1]
			total_text = pokemon+" na "+street+" "+streetno+" despawnuje sie o "+time_text+" - "+maps_text
		except Exception as e:
			total_text = "Error! |"+despawn_epoch+"|"+str(e)
			traceback.print_exc()
		return total_text

	def firefoxthread(self):
		binary = FirefoxBinary("D:\\Program Files\\Mozilla Firefox\\firefox.exe")
		browser = webdriver.Firefox(firefox_binary=binary)

		browser.get('http://localhost:5000')
		while True:
			try:
				WebDriverWait(browser, 86400).until(EC.alert_is_present(),'Timed out waiting for PA creation '+'confirmation popup to appear.')
				alert = browser.switch_to_alert()
				out_ = self.generate_output(alert.text)
				if out_:
					self.pokes.append(out_)
				try:
					print alert.text
				except UnicodeEncodeError:
					print "UnicodeEncodeError"
				alert.accept()
			except TimeoutException:
				print "no alert"

	def start(self, bot, update, args, job_queue):
		chat_id = update.message.chat_id
		try:
			due = int(args[0])
			if due < 0:
				bot.sendMessage(chat_id, text='Czas musi byc na plusie!')
				return

			job = Job(self.alarm, due, repeat=True, context=chat_id)
			self.timers[chat_id] = job
			job_queue.put(job)

			bot.sendMessage(chat_id, text='Wlaczono powiadomienia o nowych pokemonach!')

		except (IndexError, ValueError):
			bot.sendMessage(chat_id, text='Uzycie: /start <sekundy>')

	def add(self, bot, update, args):
		chat_id = update.message.chat_id
		try:
			pokemon = args[0]
			if pokemon in ('h', 'help'):
				raise ValueError()
			if pokemon not in self.wanted_pokemon:
				if pokemon not in self.fajne_poki_l:
					self.wanted_pokemon.append(pokemon)
					bot.sendMessage(chat_id, text="Dodano pokemona do listy!")
				else:
					for p_ in self.fajne_poki[pokemon]:
						self.wanted_pokemon.append(p_)
					bot.sendMessage(chat_id, text="Dodano pokemony do listy!")
			else:
				bot.sendMessage(chat_id, text="Pokemon juz jest w liscie.")
		except (IndexError, ValueError):
			bot.sendMessage(chat_id, text='Uzycie: /add <pokemon>/[rzadkie/ewolucja]')

	def remove(self, bot, update, args):
		chat_id = update.message.chat_id
		try:
			pokemon = args[0]
			if pokemon in ('h', 'help'):
				raise ValueError()
			if (pokemon in self.wanted_pokemon) or (pokemon in self.fajne_poki_l):
				if pokemon not in self.fajne_poki_l:
					self.wanted_pokemon.remove(pokemon)
					bot.sendMessage(chat_id, text="Usunieto pokemona z listy!")
				else:
					for p_ in self.fajne_poki[pokemon]:
						try:
							self.wanted_pokemon.remove(p_)
						except:
							pass
					bot.sendMessage(chat_id, text="Usunieto pokemony z listy!")
			else:
				bot.sendMessage(chat_id, text="Pokemona nie ma w liscie.")
		except (IndexError, ValueError):
			bot.sendMessage(chat_id, text='Uzycie: /remove <pokemon>/[rzadkie/ewolucja]')

	def list(self, bot, update, args):
		chat_id = update.message.chat_id
		if self.wanted_pokemon:
			poki = ', '.join(self.wanted_pokemon)
			bot.sendMessage(chat_id, text="Pokemony w liscie: "+poki)
		else:
			bot.sendMessage(chat_id, text="Nie ma zadnych pokemonow w liscie.")

	def alarm(self, bot, job):
		if self.pokes:
			text = '\n'.join(self.pokes[:5])
			del self.pokes[:5]
			bot.sendMessage(job.context, text=text)
		else:
			print "---"
		
	def error(self, bot, update, error):
		pass

	def main(self):
		updater = Updater(self.api_key)
		dp = updater.dispatcher
		dp.add_handler(CommandHandler("start", self.start, pass_args=True, pass_job_queue=True))
		dp.add_handler(CommandHandler("add", self.add, pass_args=True))
		dp.add_handler(CommandHandler("remove", self.remove, pass_args=True))
		dp.add_handler(CommandHandler("list", self.list, pass_args=True))
		dp.add_error_handler(self.error)
		updater.start_polling()
		updater.idle()


if __name__ == '__main__':
	api = "telegram api key"
	maps = "maps api key"
	a = MainHandler(api, maps)  # thread.start_new_thread(a.main, ())
	thread.start_new_thread(a.firefoxthread, ())
	a.main()