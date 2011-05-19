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
			if group.has_key('del'):
				gitosis_conf.remove_section(group['name'])
			else:
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
			"cd %s && git commit -a -m 'Add new repository %s in group %s'"%(TMP_DIR, repo_name, group_name))
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
			"cd %s && git commit -a -m 'Delete repository %s from group'"%(TMP_DIR, repo_name, group_name))
		)
		self.output.append(commands.getstatusoutput('cd %s && git push'%(TMP_DIR)))

	def add_group(self, group_name):
		if self._get_group(group_name) != None:
			raise Exception('Group %s aleady exists.'%(group_name))
		
		self.groups.append({
			'name':'group ' + group_name,
			'repos':'',
			'members':'',
		})

		self._save_config()
		self.output.append(commands.getstatusoutput(
			"cd %s && git commit -a -m 'Add new group %s'"%(TMP_DIR, group_name))
		)
		self.output.append(commands.getstatusoutput('cd %s && git push'%(TMP_DIR)))

	def del_group(self, group_name):
		group = self._get_group(group_name)
		if group == None:
			raise Exception('Group %s not found.'%(group_name))
		
		group['del'] = True

		self._save_config()
		self.output.append(commands.getstatusoutput(
			"cd %s && git commit -a -m 'Delete group %s'"%(TMP_DIR, group_name))
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

	def del_member(self, group_name, member_name):
		if self._get_key(member_name + '.pub') == None:
			raise Exception('Key for member %s not found.'%(member_name))
		
		group = self._get_group(group_name)
		if group == None:
			raise Exception('Group %s not found.'%(group_name))
			
		del group['members'][group['members'].index(member_name)]

		self._save_config()
		self.output.append(commands.getstatusoutput(
			"cd %s && git commit -a -m 'Delete member %s from group %s'"%(TMP_DIR, member_name, group_name))
		)
		self.output.append(commands.getstatusoutput('cd %s && git push'%(TMP_DIR)))

	def add_key(self, key_path, key_name):
		if self._get_key(key_name + '.pub') != None:
			raise Exception('Key %s already exists.'%(key_name))

		key = os.path.join(TMP_DIR, 'keydir', key_name+'.pub')
		self.output.append(commands.getstatusoutput(
			'cp %s %s'%(key_path, key)
		))
		
		self.output.append(commands.getstatusoutput(
			"cd %s && git add %s"%(TMP_DIR, key))
		)
		self.output.append(commands.getstatusoutput(
			"cd %s && git commit -a -m 'Add new ssh key %s'"%(TMP_DIR, key_name))
		)
		self.output.append(commands.getstatusoutput('cd %s && git push'%(TMP_DIR)))

	def del_key(self, key_name):
		if self._get_key(key_name + '.pub') == None:
			raise Exception('Key %s not found.'%(key_name))

		self.output.append(commands.getstatusoutput(
			'rm %s'%(os.path.join(TMP_DIR, 'keydir', key_name + '.pub'))
		))
		
		self.output.append(commands.getstatusoutput(
			"cd %s && git commit -a -m 'Delete ssh key %s'"%(TMP_DIR, key_name))
		)
		self.output.append(commands.getstatusoutput('cd %s && git push'%(TMP_DIR)))

	def get_config(self):
		return open(os.path.join(TMP_DIR, 'gitosis.conf')).read()

	def get_keys(self):
		return os.listdir(os.path.join(TMP_DIR, 'keydir'))
		
class ConsoleGitosisAdmin(GitosisAdmin):

	def print_repos(self):
		for item in self.groups:
			print '- %s (%s)'%(item['name'].replace('group ', ''), item['members'])
			for repo in item['repos']:
				print '    * ' + repo
	
	# Show comands
	def cmd_list(self):
		self.init(self.remote)
		self.print_repos()

	def cmd_show_config(self):
		print self.__dict__
		self.init(self.remote)
		print self.get_config()

	def cmd_show_keys(self):
		self.init(self.remote)
		print '\n'.join(self.get_keys())

	# Repository commands
	def cmd_add_repo(self):
		self.init(self.remote)
		self.add_repo(self.group, self.repo)
		self.print_repos()

	def cmd_del_repo(self):
		self.init(self.remote)
		self.del_repo(self.repo)
		self.print_repos()	

	# Repository group commands
	def cmd_add_group(self):
		self.init(self.remote)
		self.add_group(self.group)
		self.print_repos()

	def cmd_del_group(self):
		self.init(self.remote)
		self.del_group(self.group)
		self.print_repos()

	# Member commands
	def cmd_add_member(self):
		self.init(self.remote)
		self.add_member(self.group, self.member)
		self.print_repos()

	def cmd_del_member(self):
		self.init(self.remote)
		self.del_member(self.group, self.member)
		self.print_repos()

	# ssh key commands
	def cmd_add_key(self):
		self.init(self.remote)
		self.add_key(self.key, self.name)
		print self.get_keys()

	def cmd_del_key(self):
		self.init(self.remote)
		self.del_key(self.name)
		print self.get_keys()

	def __init__(self):
		parser = argparse.ArgumentParser(description='Gitosis remote repository admin tool.')
		subparsers = parser.add_subparsers(help='commands')
	
		list_parser = subparsers.add_parser('list', help='List repositories')
		list_parser.add_argument('remote', action='store', help='Repository hostname')
		list_parser.set_defaults(func=self.cmd_list)

		show_config_parser = subparsers.add_parser('show-config', help='Show gitosis.conf file')
		show_config_parser.add_argument('--remote', '-r', action='store', help='Repository hostname')
		show_config_parser.set_defaults(func=self.cmd_show_config)

		show_keys_parser = subparsers.add_parser('show-keys', help='Show ssh keys')
		show_keys_parser.add_argument('--remote', '-r', action='store', help='Repository hostname')
		show_keys_parser.set_defaults(func=self.cmd_show_keys)

		add_repo_parser = subparsers.add_parser('add-repo', help='Add repository')
		add_repo_parser.add_argument('repo', action='store', help='Repository name')		
		add_repo_parser.add_argument('--group', '-g', action='store', help='Repository group')
		add_repo_parser.add_argument('--remote', '-r', action='store', help='Repository hostname')
		add_repo_parser.set_defaults(func=self.cmd_add_repo)

		del_repo_parser = subparsers.add_parser('del-repo', help='Delete repository')
		del_repo_parser.add_argument('repo', action='store', help='Repository name')		
		del_repo_parser.add_argument('--remote', '-r', action='store', help='Repository hostname')
		del_repo_parser.set_defaults(func=self.cmd_del_repo)		

		add_group_parser = subparsers.add_parser('add-group', help='Add repository group')
		add_group_parser.add_argument('group', action='store', help='Repository group')
		add_group_parser.add_argument('--remote', '-r', action='store', help='Repository hostname')
		add_group_parser.set_defaults(func=self.cmd_add_group)

		del_group_parser = subparsers.add_parser('del-group', help='Delete repository group')
		del_group_parser.add_argument('group', action='store', help='Repository group')
		del_group_parser.add_argument('--remote', '-r', action='store', help='Repository hostname')
		del_group_parser.set_defaults(func=self.cmd_del_group)

		add_member_parser = subparsers.add_parser('add-member', help='Add member to group')
		add_member_parser.add_argument('member', action='store', help='Group member')
		add_member_parser.add_argument('--group', '-g', action='store', help='Repository group')
		add_member_parser.add_argument('--remote', '-r', action='store', help='Repository hostname')
		add_member_parser.set_defaults(func=self.cmd_add_member)

		del_member_parser = subparsers.add_parser('del-member', help='Delete member from group')
		del_member_parser.add_argument('member', action='store', help='Group member')
		del_member_parser.add_argument('--group', '-g', action='store', help='Repository group')
		del_member_parser.add_argument('--remote', '-r', action='store', help='Repository hostname')
		del_member_parser.set_defaults(func=self.cmd_del_member)

		add_key_parser = subparsers.add_parser('add-key', help='Add new public ssh key')
		add_key_parser.add_argument('key', action='store', help='Public ssh key file')
		add_key_parser.add_argument('--name', '-n', action='store', help='Key name')
		add_key_parser.add_argument('--remote', '-r', action='store', help='Repository hostname')
		add_key_parser.set_defaults(func=self.cmd_add_key)

		del_key_parser = subparsers.add_parser('del-key', help='Delete ssh key file and members from groups')
		del_key_parser.add_argument('name', action='store', help='Key name')
		del_key_parser.add_argument('--remote', '-r', action='store', help='Repository hostname')
		del_key_parser.set_defaults(func=self.cmd_del_key)

		parser.parse_args(namespace=self)
		self.func()

def main():
	ConsoleGitosisAdmin()

if __name__ == "__main__":
	main()
