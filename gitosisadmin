#!/usr/bin/env python2.7

import commands
import getopt, sys, os
import ConfigParser
import argparse

GITOSIS_DIR = 'gitosis-admin'
TMP_DIR = '/tmp/' + GITOSIS_DIR

class GitosisAdmin(object):

	hostname = None
	groups = []
	output = []

	def init(self, hostname):
		self.hostname = hostname

		if os.path.exists(TMP_DIR):
			self._clean_temp()

		self.output.append(commands.getstatusoutput('git clone %s:%s.git %s'%(self.hostname,GITOSIS_DIR,TMP_DIR)))
		self._load_config()

	def __del__(self):
		self._clean_temp()

	def _clean_temp(self):
		self.output.append(commands.getstatusoutput('rm -rf %s'%(TMP_DIR)))

	def _load_config(self):
		gitosis_conf = ConfigParser.RawConfigParser()
		gitosis_conf.read(TMP_DIR + '/gitosis.conf')
		for section in gitosis_conf.sections():
			if section != 'gitosis':
				self.groups.append({
					'name':section,
					'repos':gitosis_conf.get(section, 'writable').split(),
					'members':gitosis_conf.get(section, 'members').split(),
				})

	def _save_config(self):
		gitosis_conf = ConfigParser.RawConfigParser()
		gitosis_conf.read(TMP_DIR + '/gitosis.conf')
		for group in self.groups:
			if not gitosis_conf.has_section(group['name']):
				gitosis_conf.add_section(group['name'])
			gitosis_conf.set(group['name'], 'writable', ' '.join(group['repos']))
			gitosis_conf.set(group['name'], 'members', ' '.join(group['members']))

		with open(TMP_DIR + '/gitosis.conf', 'wb') as configfile:
			gitosis_conf.write(configfile)

	def _get_repo(self, repo_name):
		for group in self.groups:
			for repo in group['repos']:
				if repo == repo_name:
					return repo
		return None

	def _get_key(self, key_name):
		keys = os.listdir(os.path.join(TMP_DIR, 'keydir'))
		for key in keys:
			if key == key_name:
				return key
		return None

	def _get_group(self, group_name):
		for group in self.groups:
			if group['name'].replace('group ', '') == group_name:
				return group
		return None		

	def add_repo(self, group_name, repo_name):
		if self._get_repo(repo_name) != None:
			raise Exception('Repository %s aleady exists.'%(repo_name))

		group = self._get_group(group_name)
		if group == None:
			raise Exception('Group %s not found.'%(group_name))
			
		group['repos'].append(repo_name)
		self._save_config()
		self.output.append(commands.getstatusoutput(
			"cd %s && git commit -a -m 'Add new repository %s'"%(TMP_DIR, repo_name))
		)
		self.output.append(commands.getstatusoutput('cd %s && git push'%(TMP_DIR)))

	def del_repo(self, repo_name):
		if self._get_repo(repo_name) == None:
			raise Exception('Repository %s not found.'%(repo_name))
		
		for group in self.groups:
			for repo in group['repos']:
				if repo == repo_name:
					del group['repos'][group['repos'].index(repo)]
		
		self._save_config()
		self.output.append(commands.getstatusoutput(
			"cd %s && git commit -a -m 'Delete repository %s'"%(TMP_DIR, repo_name))
		)
		self.output.append(commands.getstatusoutput('cd %s && git push'%(TMP_DIR)))

	def add_group(self, group_name):
		if self._get_group(group_name) != None:
			raise Exception('Group %s aleady exists.'%(group_name))
		
		self.groups.append({
			'name':group_name,
			'repos':'',
			'members':'',
		})

		self._save_config()
		self.output.append(commands.getstatusoutput(
			"cd %s && git commit -a -m 'Add new group %s'"%(TMP_DIR, group_name))
		)
		self.output.append(commands.getstatusoutput('cd %s && git push'%(TMP_DIR)))

	def add_member(self, group_name, member_name):
		if self._get_key(member_name + '.pub') == None:
			raise Exception('Key for member %s not found.'%(member_name))
		
		group = self._get_group(group_name)
		if group == None:
			raise Exception('Group %s not found.'%(group_name))
			
		group['members'].append(member_name)

		self._save_config()
		self.output.append(commands.getstatusoutput(
			"cd %s && git commit -a -m 'Add new member %s to group %s'"%(TMP_DIR, member_name, group_name))
		)
		self.output.append(commands.getstatusoutput('cd %s && git push'%(TMP_DIR)))

	def get_config(self):
		return open(os.path.join(TMP_DIR, 'gitosis.conf')).read()

	def get_keys(self):
		return os.listdir(os.path.join(TMP_DIR, 'keydir'))
		
class ConsoleGitosisAdmin(GitosisAdmin):
	
	def cmd_list(self):
		self.init(self.host)
		for item in self.groups:
			print '- %s (%s)'%(item['name'].replace('group ', ''), item['members'])
			for repo in item['repos']:
				print '    * ' + repo

	def cmd_add_repo(self):
		self.init(self.host)
		self.add_repo(self.group, self.repo)

	def cmd_del_repo(self):
		self.init(self.host)
		self.del_repo(self.repo)		

	def cmd_add_group(self):
		self.init(self.host)
		self.add_group(self.group)

	def cmd_add_member(self):
		self.init(self.host)
		self.add_member(self.group, self.member)

	def cmd_show_config(self):
		self.init(self.host)
		print self.get_config()

	def cmd_show_keys(self):
		self.init(self.host)
		print '\n'.join(self.get_keys())

	def __init__(self):
		parser = argparse.ArgumentParser(description='Gitosis remote repository admin tool.')
		subparsers = parser.add_subparsers(help='commands')
	
		list_parser = subparsers.add_parser('list', help='List repositories')
		list_parser.add_argument('host', action='store', help='Repository hostname')
		list_parser.set_defaults(func=self.cmd_list)

		show_config_parser = subparsers.add_parser('show_config', help='Show gitosis.conf file')
		show_config_parser.add_argument('host', action='store', help='Repository hostname')
		show_config_parser.set_defaults(func=self.cmd_show_config)

		show_keys_parser = subparsers.add_parser('show_keys', help='Show ssh keys')
		show_keys_parser.add_argument('host', action='store', help='Repository hostname')
		show_keys_parser.set_defaults(func=self.cmd_show_keys)

		add_repo_parser = subparsers.add_parser('add-repo', help='Add repository')
		add_repo_parser.add_argument('repo', action='store', help='Repository name')		
		add_repo_parser.add_argument('-group', action='store', help='Repository group')
		add_repo_parser.add_argument('-host', action='store', help='Repository hostname')
		add_repo_parser.set_defaults(func=self.cmd_add_repo)

		del_repo_parser = subparsers.add_parser('del-repo', help='Del repository')
		del_repo_parser.add_argument('repo', action='store', help='Repository name')		
		del_repo_parser.add_argument('-host', action='store', help='Repository hostname')
		del_repo_parser.set_defaults(func=self.cmd_del_repo)		

		add_group_parser = subparsers.add_parser('add-group', help='Add repository group')
		add_group_parser.add_argument('group', action='store', help='Repository group')
		add_group_parser.add_argument('-host', action='store', help='Repository hostname')
		add_group_parser.set_defaults(func=self.cmd_add_group)

		add_member_parser = subparsers.add_parser('add-member', help='Add member to group')
		add_member_parser.add_argument('member', action='store', help='Group member')
		add_member_parser.add_argument('-group', action='store', help='Repository group')
		add_member_parser.add_argument('-host', action='store', help='Repository hostname')
		add_member_parser.set_defaults(func=self.cmd_add_member)

		parser.parse_args(namespace=self)
		self.func()

def main():
	ConsoleGitosisAdmin()

if __name__ == "__main__":
	main()
