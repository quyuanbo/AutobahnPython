###############################################################################
##
##  Copyright (C) 2014 Tavendo GmbH
##
##  Licensed under the Apache License, Version 2.0 (the "License");
##  you may not use this file except in compliance with the License.
##  You may obtain a copy of the License at
##
##      http://www.apache.org/licenses/LICENSE-2.0
##
##  Unless required by applicable law or agreed to in writing, software
##  distributed under the License is distributed on an "AS IS" BASIS,
##  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
##  See the License for the specific language governing permissions and
##  limitations under the License.
##
###############################################################################

from __future__ import absolute_import

__all__ = ['ApplicationSession',
           'ApplicationSessionFactory',
           'RouterSession',
           'RouterSessionFactory']

from autobahn.wamp import protocol

import asyncio
from asyncio.tasks import iscoroutine
from asyncio import Future



class FutureMixin:
   """
   Mixin for Asyncio style Futures.
   """

   def _create_future(self):
      return Future()

   def _as_future(self, fun, *args, **kwargs):
      try:
         res = fun(*args, **kwargs)
      except Exception as e:
         f = Future()
         f.set_exception(e)
         return f
      else:
         if isinstance(res, Future):
            return res
         elif iscoroutine(res):
            return asyncio.Task(res)
         else:
            f = Future()
            f.set_result(res)
            return f

   def _resolve_future(self, future, value):
      future.set_result(value)

   def _reject_future(self, future, value):
      future.set_exception(value)

   def _add_future_callbacks(self, future, callback, errback):
      def done(f):
         try:
            res = f.result()
            callback(res)
         except Exception as e:
            errback(e)
      return future.add_done_callback(done)

   def _gather_futures(self, futures, consume_exceptions = True):
      return asyncio.gather(*futures, return_exceptions = consume_exceptions)



class ApplicationSession(FutureMixin, protocol.ApplicationSession):
   """
   WAMP application session for asyncio-based applications.
   """


class ApplicationSessionFactory(FutureMixin, protocol.ApplicationSessionFactory):
   """
   WAMP application session factory for asyncio-based applications.
   """


class RouterSession(FutureMixin, protocol.RouterSession):
   """
   WAMP router session for asyncio-based applications.
   """


class RouterSessionFactory(FutureMixin, protocol.RouterSessionFactory):
   """
   WAMP router session factory for asyncio-based applications.
   """
   session = RouterSession


import sys
import traceback
import asyncio
from autobahn.wamp.types import ComponentConfig
from autobahn.asyncio.websocket import WampWebSocketClientFactory


class ApplicationRunner:

   def __init__(self, endpoint, url, realm, extra = {}, debug = False,
      debug_wamp = False, debug_app = False):
      self.endpoint = endpoint
      self.url = url
      self.realm = realm
      self.extra = extra
      self.debug = debug
      self.debug_wamp = debug_wamp
      self.debug_app = debug_app
      self.make = None


   def run(self, make):
      ## 1) factory for use ApplicationSession
      def create():
         cfg = ComponentConfig(self.realm, self.extra)
         try:
            session = make(cfg)
         except Exception as e:
            ## the app component could not be created .. fatal
            print(traceback.format_exc())
            asyncio.get_event_loop().stop()

         session.debug_app = self.debug_app
         return session

      ## 2) create a WAMP-over-WebSocket transport client factory
      transport_factory = WampWebSocketClientFactory(create, url = self.url,
         debug = self.debug, debug_wamp = self.debug_wamp)

      ## 3) start the client
      loop = asyncio.get_event_loop()
      coro = loop.create_connection(transport_factory, args.host, args.port)
      loop.run_until_complete(coro)

      ## 4) now enter the asyncio event loop
      loop.run_forever()
      loop.close()
