#!/usr/bin/env python3
from telegram import Updater
import derpibooru
import traceback
import sys
import random
import datetime
import os

class Spitfire:
    adminid = None
    debug_chat_id = adminid
    openlogs = {}
    _upd = None

    def __init__(self, token, adminid):
        self.adminid = adminid
        self._upd = Updater(token=token)
        self._upd.dispatcher.addTelegramMessageHandler(
                lambda bot, update, args: self.exceptionhook(self.onMessage, bot, update, None))
        self._upd.dispatcher.addTelegramCommandHandler(
                "start", lambda bot, update, args: self.exceptionhook(self.start, bot, update, None))
        self._upd.dispatcher.addTelegramCommandHandler(
                "derpibooru", lambda bot, update, args: self.exceptionhook(self.derpibooru_lookup, bot, update, args))
        self._upd.dispatcher.addTelegramCommandHandler(
                "advanced", lambda bot, update, args, **kwargs: self.exceptionhook(self.help, bot, update, None))
        self._upd.dispatcher.addTelegramCommandHandler(
                "debug", lambda bot, update, args: self.exceptionhook(self.debug, bot, update, args))

        self._upd.start_polling()

    def exceptionhook(self, target, bot, update, args):
        try:
            if self.onMessage != target:
                self.onMessage(bot, update)
            if args is None:
                print("Calling {}({}, {})".format(target, bot, update))
                target(bot, update)
            else:
                print("Calling {}({}, {}, {})".format(target, bot, update, args))
                target(bot, update, args)
        except Exception as exception:
            if (exception != KeyboardInterrupt) and (self.debug_chat_id is not None):
                self._upd.bot.sendMessage(chat_id=self.debug_chat_id, text="aww shite, exception occured, details"
                                                                           " coming up, boss")
                exc_type, exc_value, exc_traceback = sys.exc_info()
                self._upd.bot.sendMessage(chat_id=self.debug_chat_id, text="".join(traceback.format_exception(
                        exc_type, exc_value, exc_traceback)))
            else:
                raise exception

    def start(self, bot, update):
        bot.sendMessage(chat_id=update.message.chat_id, text="Sup. Check /advanced because BotFather is stupid.")
        bot.sendMessage(chat_id=update.message.chat_id, text="Actually, let me do that for you.")
        self.help(bot, update)

    def help(self, bot, update):
        bot.sendMessage(chat_id=update.message.chat_id, text="""derpibooru - send an image that was recently uploaded to derpiboo.ru
derpibooru search <search query> - send an image from a search on derpiboo.ru
derpibooru select - show available tag lists
derpibooru select <list> - send a random image from the tags of the selected list""")

    def onMessage(self, bot, update):
        if update.message.chat_id not in self.openlogs:
            self.openlogs[update.message.chat_id] = open("{}.bobot.log".format(update.message.chat_id),
                                                         mode="at")
        print("{:[%d/%m/%Y - %H:%M]} <{}> {}".format(
            datetime.datetime.utcnow(), update.message.from_user.username, update.message.text
        ), file=self.openlogs[update.message.chat_id])
        self.openlogs[update.message.chat_id].flush()

    def derpibooru_lookup(self, bot, update, args=list()):
        def _process_imgs(bot, update, imgs):
            if len(imgs) > 0:
                pick = random.choice(imgs)
                bot.sendPhoto(chat_id=update.message.chat_id, photo=pick.image)
                bot.sendMessage(chat_id=update.message.chat_id, text=("sauce: {}\n"
                                                                      "This image is #{}, randomly selected"
                                                                      " from the latest 10 of {} images.").format(
                        pick.url, pick.scope["this"], pick.scope["total"]))
            else:
                bot.sendMessage(chat_id=update.message.chat_id, text="nope, found zilch, zero, nada.")

        if len(args) == 0:
            imgs = []
            for image in derpibooru.Search().filter("56027").limit(10):
                imgs.append(image)
            _process_imgs(bot, update, imgs)
        elif args[0] == "select":
            bot.sendMessage(chat_id=update.message.chat_id, text="There are currently no lists available.")
        elif args[0] == "search" and len(args) == 1:
            bot.sendMessage(chat_id=update.message.chat_id, text="jesus how could you fuck this up, RTFM")
        elif args[0] == "search":
            imgs = []
            for image in derpibooru.Search().filter("56027").limit(10).query(" ".join(args[1:])):
                imgs.append(image)
            _process_imgs(bot, update, imgs)
        else:
            bot.sendMessage(chat_id=update.message.chat_id, text="you dun fucked up, you probably meant to search")

    def debug(self, bot, update, args=list()):
        if "here" in args:
            if update.message.from_user.id != self.adminid:
                bot.sendMessage(chat_id=update.message.chat_id, text="nice try, i ain't seeing you managing this soon")
            else:
                self.debug_chat_id = update.message.chat_id
                bot.sendMessage(chat_id=update.message.chat_id, text="aight, expect debug spam in the future")
        elif "info" in args:
            bot.sendMessage(chat_id=update.message.chat_id, text=("this chat has the ID {}, "
                                                                  "debug room has ID {}")
                            .format(update.message.chat_id, self.debug_chat_id))
        else:
            bot.sendMessage(chat_id=update.message.chat_id, text=
                            "super secret debug menu\n"
                            "\n"
                            "/debug here - print debug info here\n"
                            "/debug info - print some internals")
            bot.sendMessage(chat_id=update.message.chat_id, text="{}".format(args))

if "TELEGRAMKEY" not in os.environ or "TELEGRAMADMIN" not in os.environ:
    print("Set $TELEGRAMKEY to the Telegram Bot API key, and then start the bot.")
    print("Set $TELEGRAMADMIN to the chat ID of the Admin user, and then start the bot.")
    exit(1)
Spitfire(token=os.environ["TELEGRAMKEY"], adminid=int(os.environ["TELEGRAMADMIN"]))
