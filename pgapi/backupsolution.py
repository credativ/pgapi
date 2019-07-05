
class backupsolution:
    """Virtual Parent for all Backups
    Highlevel-API:
        @list_backups( cluster_identifier=None,  backup_identifier=None)
        @take_backup(kind,cluster_identifier=None)
        @remove_backup(kind,backup_identifier=None)

        @check(cluster_identifier=None)

        @add_cluster(cluster_identifier=None)
        @remove_cluster(cluster_identifier=None)

    Childs should override:

        @list_backups(self,cluster_identifier=None,  backup_identifier=None)
        @_take_full_backup(self,cluster_identifier=None)
        @_take_incremental_backup(self,cluster_identifier=None)
        @_take_logical_backup(self,cluster_identifier=None)
        @_remove_full_backup(self,backup_identifier=None)
        @_remove_incremental_backup(self,backup_identifier=None)
        @_remove_logical_backup(self,backup_identifier=None)

    """

    def list_backups(self, cluster_identifier=None,  backup_identifier=None):
        """
            { "Clusteridentifier: { "Backupidentifier": {},..}, ..}
            In the event of zero existing backups a cluster will be listed
            as toplevel in list_backups. Hence it is sufficient to have list_backups
            and omit a list_clusters function.
        """
        backupsolution._warn_not_implemented("list-backups")


    def add_cluster(self, cluster_identifier=None):
        backupsolution._warn_not_implemented("add cluster")

    def remove_cluster(cluster_identifier=None):
        backupsolution._warn_not_implemented("remove cluster")

    def check(self, cluster_identifier=None,  backup_identifier=None):
        backupsolution._warn_not_implemented("check")

    def remove_backup(self, kind='full', backup_identifier=None):
        """Currently 3 Kinds of backups are supported:
            * full - full physical
            * incremental - incremental physical
            * logical - logical
        """
        if kind == 'full':
            self._remove_full_backup(backup_identifier)
        elif kind == 'incremental':
            self._remove_incremental_backup(backup_identifier)
        elif kind == 'logical':
            self._remove_logical_backup(backup_identifier)

    def take_backup(self, kind='full', cluster_identifier=None,  backup_identifier=None):
        """Currently 3 Kinds of backups are supported:
            * full - full physical
            * incremental - incremental physical
            * logical - logical
        """
        if kind == 'full':
            self._take_full_backup(cluster_identifier)
        elif kind == 'incremental':
            self._take_incremental_backup(cluster_identifier)
        elif kind == 'logical':
            self._take_logical_backup(cluster_identifier)
        else:
            backupsolution._warn_not_implemented(f"undefined backupmethod {kind}")

    def _take_full_backup(self, cluster_identifier=None,):
        backupsolution._warn_not_implemented('FULL-BACKUP')

    def _take_incremental_backup(self, cluster_identifier=None,):
        backupsolution._warn_not_implemented('INCREMENTAL-BACKUP')

    def _take_logical_backup(self, cluster_identifier=None, ):
        backupsolution._warn_not_implemented('LOGICAL-BACKUP')

    @staticmethod
    def _warn_not_implemented(service):
        raise Exception(service+" is not supported")
