# -*- coding: utf-8 -*-

###########################################################################
## Python code generated with wxFormBuilder (version 3.9.0 Oct  8 2020)
## http://www.wxformbuilder.org/
##
## PLEASE DO *NOT* EDIT THIS FILE!
###########################################################################

import wx
import wx.xrc

###########################################################################
## Class VQCPumpUI
###########################################################################

class VQCPumpUI ( wx.Frame ):

	def __init__( self, parent ):
		wx.Frame.__init__ ( self, parent, id = wx.ID_ANY, title = u"QCPump", pos = wx.DefaultPosition, size = wx.Size( 640,448 ), style = wx.DEFAULT_FRAME_STYLE|wx.TAB_TRAVERSAL )

		self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )

		bSizer1 = wx.BoxSizer( wx.VERTICAL )

		self.main_panel = wx.Panel( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		bSizer3 = wx.BoxSizer( wx.VERTICAL )

		bSizer4 = wx.BoxSizer( wx.HORIZONTAL )


		bSizer4.Add( ( 0, 0), 1, wx.EXPAND, 5 )

		self.do_pump_on_startup = wx.CheckBox( self.main_panel, wx.ID_ANY, u"Run Pumps On Launch", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.do_pump_on_startup.SetToolTip( u"Check this to automatically start pumps when QCPump is launched" )

		bSizer4.Add( self.do_pump_on_startup, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )

		self.add_pump = wx.Button( self.main_panel, wx.ID_ANY, u"Add Pump", wx.DefaultPosition, wx.DefaultSize, 0 )

		self.add_pump.SetBitmap( wx.NullBitmap )
		bSizer4.Add( self.add_pump, 0, wx.ALL, 5 )

		self.run_pumps = wx.ToggleButton( self.main_panel, wx.ID_ANY, u"Run Pumps", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.run_pumps.SetLabelMarkup( u"Run Pumps" )
		self.run_pumps.SetBitmap( wx.NullBitmap )
		self.run_pumps.SetBitmapPosition( wx.LEFT )
		bSizer4.Add( self.run_pumps, 0, wx.ALL, 5 )


		bSizer3.Add( bSizer4, 0, wx.EXPAND, 5 )

		self.pump_notebook = wx.Notebook( self.main_panel, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, 0 )

		bSizer3.Add( self.pump_notebook, 1, wx.EXPAND |wx.ALL, 5 )


		self.main_panel.SetSizer( bSizer3 )
		self.main_panel.Layout()
		bSizer3.Fit( self.main_panel )
		bSizer1.Add( self.main_panel, 1, wx.EXPAND|wx.ALL, 5 )


		self.SetSizer( bSizer1 )
		self.Layout()
		self.status_bar = self.CreateStatusBar( 1, wx.STB_SIZEGRIP, wx.ID_ANY )
		self.menu_bar = wx.MenuBar( wx.MB_DOCKABLE )
		self.file = wx.Menu()
		self.about = wx.MenuItem( self.file, wx.ID_ANY, u"&About", u"Information about the QCPump Application", wx.ITEM_NORMAL )
		self.file.Append( self.about )

		self.file.AppendSeparator()

		self.quit = wx.MenuItem( self.file, wx.ID_ANY, u"&Quit", u"Exit QCPump", wx.ITEM_NORMAL )
		self.file.Append( self.quit )

		self.menu_bar.Append( self.file, u"&File" )

		self.SetMenuBar( self.menu_bar )


		self.Centre( wx.BOTH )

		# Connect Events
		self.Bind( wx.EVT_ACTIVATE, self.OnActivate )
		self.Bind( wx.EVT_ACTIVATE_APP, self.OnActivateApp )
		self.Bind( wx.EVT_CLOSE, self.OnClose )
		self.Bind( wx.EVT_IDLE, self.OnIdle )
		self.Bind( wx.EVT_SHOW, self.OnShow )
		self.do_pump_on_startup.Bind( wx.EVT_CHECKBOX, self.OnPumpOnStartup )
		self.add_pump.Bind( wx.EVT_BUTTON, self.OnAddPump )
		self.run_pumps.Bind( wx.EVT_TOGGLEBUTTON, self.OnRunPumpsToggle )
		self.Bind( wx.EVT_MENU, self.OnAbout, id = self.about.GetId() )
		self.Bind( wx.EVT_MENU, self.OnQuit, id = self.quit.GetId() )

	def __del__( self ):
		pass


	# Virtual event handlers, overide them in your derived class
	def OnActivate( self, event ):
		event.Skip()

	def OnActivateApp( self, event ):
		event.Skip()

	def OnClose( self, event ):
		event.Skip()

	def OnIdle( self, event ):
		event.Skip()

	def OnShow( self, event ):
		event.Skip()

	def OnPumpOnStartup( self, event ):
		event.Skip()

	def OnAddPump( self, event ):
		event.Skip()

	def OnRunPumpsToggle( self, event ):
		event.Skip()

	def OnAbout( self, event ):
		event.Skip()

	def OnQuit( self, event ):
		event.Skip()


###########################################################################
## Class VStatusPanel
###########################################################################

class VStatusPanel ( wx.Panel ):

	def __init__( self, parent, id = wx.ID_ANY, pos = wx.DefaultPosition, size = wx.Size( 500,300 ), style = wx.TAB_TRAVERSAL, name = wx.EmptyString ):
		wx.Panel.__init__ ( self, parent, id = id, pos = pos, size = size, style = style, name = name )

		bSizer9 = wx.BoxSizer( wx.VERTICAL )

		sizer = wx.FlexGridSizer( 3, 2, 0, 0 )
		sizer.AddGrowableCol( 1 )
		sizer.AddGrowableRow( 2 )
		sizer.SetFlexibleDirection( wx.BOTH )
		sizer.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )

		self.status_label = wx.StaticText( self, wx.ID_ANY, u"Status:", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.status_label.Wrap( -1 )

		sizer.Add( self.status_label, 0, wx.ALL|wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 5 )

		self.status = wx.StaticText( self, wx.ID_ANY, u"Not running", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.status.Wrap( -1 )

		sizer.Add( self.status, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )

		self.progress_label = wx.StaticText( self, wx.ID_ANY, u"Progress:", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.progress_label.Wrap( -1 )

		sizer.Add( self.progress_label, 0, wx.ALL|wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 5 )

		self.progress = wx.Gauge( self, wx.ID_ANY, 100, wx.DefaultPosition, wx.DefaultSize, wx.GA_HORIZONTAL )
		self.progress.SetValue( 0 )
		sizer.Add( self.progress, 0, wx.ALL|wx.EXPAND, 5 )

		self.log_label = wx.StaticText( self, wx.ID_ANY, u"Logging:", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.log_label.Wrap( -1 )

		sizer.Add( self.log_label, 1, wx.ALL|wx.EXPAND|wx.ALIGN_RIGHT, 5 )


		bSizer9.Add( sizer, 0, wx.EXPAND, 5 )


		self.SetSizer( bSizer9 )
		self.Layout()

	def __del__( self ):
		pass


###########################################################################
## Class VAddPumpDialog
###########################################################################

class VAddPumpDialog ( wx.Dialog ):

	def __init__( self, parent ):
		wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = u"Add a new Pump", pos = wx.DefaultPosition, size = wx.Size( 463,183 ), style = wx.DEFAULT_DIALOG_STYLE )

		self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )

		bSizer5 = wx.BoxSizer( wx.VERTICAL )

		fgSizer2 = wx.FlexGridSizer( 4, 2, 0, 0 )
		fgSizer2.AddGrowableCol( 1 )
		fgSizer2.SetFlexibleDirection( wx.BOTH )
		fgSizer2.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )

		self.pump_type_label = wx.StaticText( self, wx.ID_ANY, u"Pump Type", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.pump_type_label.Wrap( -1 )

		fgSizer2.Add( self.pump_type_label, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.TOP|wx.RIGHT|wx.LEFT, 5 )

		pump_typeChoices = []
		self.pump_type = wx.Choice( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, pump_typeChoices, wx.CB_SORT )
		self.pump_type.SetSelection( 0 )
		fgSizer2.Add( self.pump_type, 0, wx.TOP|wx.RIGHT|wx.LEFT|wx.EXPAND, 5 )


		fgSizer2.Add( ( 0, 0), 1, wx.EXPAND, 5 )

		self.pump_type_help = wx.StaticText( self, wx.ID_ANY, u"Select the Pump Type to Add", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.pump_type_help.Wrap( -1 )

		self.pump_type_help.SetFont( wx.Font( wx.NORMAL_FONT.GetPointSize(), wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString ) )

		fgSizer2.Add( self.pump_type_help, 0, wx.BOTTOM|wx.RIGHT|wx.LEFT, 5 )

		self.pump_name_label = wx.StaticText( self, wx.ID_ANY, u"Pump Name", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.pump_name_label.Wrap( -1 )

		fgSizer2.Add( self.pump_name_label, 0, wx.ALIGN_RIGHT|wx.TOP|wx.RIGHT|wx.LEFT|wx.ALIGN_CENTER_VERTICAL, 5 )

		self.pump_name = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		self.pump_name.SetMaxLength( 0 )
		fgSizer2.Add( self.pump_name, 0, wx.EXPAND|wx.TOP|wx.RIGHT|wx.LEFT, 5 )


		fgSizer2.Add( ( 0, 0), 1, wx.EXPAND, 5 )

		self.pump_name_help = wx.StaticText( self, wx.ID_ANY, u"Give this pump  a unique name", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.pump_name_help.Wrap( -1 )

		self.pump_name_help.SetFont( wx.Font( wx.NORMAL_FONT.GetPointSize(), wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString ) )

		fgSizer2.Add( self.pump_name_help, 0, wx.ALL, 5 )


		bSizer5.Add( fgSizer2, 0, wx.EXPAND, 5 )

		m_sdbSizer1 = wx.StdDialogButtonSizer()
		self.m_sdbSizer1OK = wx.Button( self, wx.ID_OK )
		m_sdbSizer1.AddButton( self.m_sdbSizer1OK )
		self.m_sdbSizer1Cancel = wx.Button( self, wx.ID_CANCEL )
		m_sdbSizer1.AddButton( self.m_sdbSizer1Cancel )
		m_sdbSizer1.Realize();

		bSizer5.Add( m_sdbSizer1, 0, wx.EXPAND|wx.ALL, 5 )


		self.SetSizer( bSizer5 )
		self.Layout()

		self.Centre( wx.BOTH )

		# Connect Events
		self.pump_type.Bind( wx.EVT_CHOICE, self.OnPumpTypeChange )
		self.m_sdbSizer1OK.Bind( wx.EVT_BUTTON, self.OnOk )

	def __del__( self ):
		pass


	# Virtual event handlers, overide them in your derived class
	def OnPumpTypeChange( self, event ):
		event.Skip()

	def OnOk( self, event ):
		event.Skip()


