#!/usr/bin/tclsh
#
#

package provide awdark 7.9

set ap [file normalize [file dirname [info script]]]
if { $ap ni $::auto_path } {
  lappend ::auto_path $ap
}
set ap [file normalize [file join [file dirname [info script]] .. code]]
if { $ap ni $::auto_path } {
  lappend ::auto_path $ap
}
unset ap
package require awthemes

namespace eval ::ttk::theme::awdark {

  proc setBaseColors { } {
    variable colors

    array set colors {
        style.arrow           solid-bg
        style.checkbutton     roundedrect-check
        style.combobox        solid-bg
        style.menubutton      solid
        style.radiobutton     circle-circle-hlbg
        style.treeview        solid
        bg.bg                 #33393b
        fg.fg                 #ffffff
        graphics.color        #215d9c
        is.dark               true
    }
  }

  proc setDerivedColors { } {
    variable colors

    set colors(border) #000000
    set colors(button) $colors(bg.darker)
    set colors(button.active) $colors(bg.light)
    set colors(tab.active) $colors(bg.darker)
    set colors(border.tab) $colors(bg.light)
    set colors(tab.disabled) $colors(bg.darker)
    set colors(tab.inactive) $colors(bg.darker)
    set colors(tab.selected) $colors(bg.darker)
    set colors(button.anchor) {}
    set colors(button.padding) {5 3}
    set colors(entrybg.bg) $colors(bg.darkest)
    set colors(entry.padding) {5 1}
    set colors(arrow.color) $colors(fg.fg)
    set colors(scrollbar.color.grip) #000000
    set colors(spinbox.color.bg) $colors(graphics.color)
    set colors(menubutton.padding) {5 2}
    set colors(notebook.tab.focusthickness) 5
    set colors(border.scale) $colors(bg.darkest)
    set colors(select.bg) $colors(graphics.color)
    set colors(tab.use.topbar) true
    set colors(trough.color) $colors(bg.darkest)
  }

  proc init { } {
    ::ttk::awthemes::init awdark
  }

  init
}
