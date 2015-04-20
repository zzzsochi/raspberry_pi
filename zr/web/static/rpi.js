var rpiApp = angular.module('RpiApp', ['ngResource']);


rpiApp.controller('MPDCtrl', function ($scope, $resource, $timeout) {
    $scope.status = {};
    $scope.playlist = [];

    var mpdService = $resource('/mpd', {}, {
        send: {method: 'POST'}
    });

    var mpdPlaylist = $resource('/mpd/playlist', {}, {
        list: {isArray: true},
        add: {method: 'POST', isArray: true}
    });


    $scope.statusRefresh = function () {
        var mpdStatus = $resource('/mpd');
        mpdStatus.get(function (res) {
            $scope.status = res;
        });
    }

    $scope.playlistRefresh = function () {
        mpdPlaylist.list(function (res) {
            $scope.playlist = res;
        });
    }

    $scope.refresh = function () {
        console.log('refresh')
        $scope.statusRefresh();
        $scope.playlistRefresh();
    }

    $scope.refreshCycle = function (interval) {
        $scope.refresh();
        $timeout(function () {$scope.refreshCycle(interval)}, interval);
    }

    $scope.sendAction = function (action) {
        mpdService.send({'action': action});
        $scope.statusRefresh();
    }

    $scope.play = function (id) {
        var mpdPlaylistSong = $resource('/mpd/playlist/:id',
            {id: id},
            {play: {method: 'PUT'}}
        );

        mpdPlaylistSong.play({action: 'play'}, function () {
            $scope.refresh()
            $timeout($scope.refresh, 1000);
            $timeout($scope.refresh, 2000);
            $timeout($scope.refresh, 5000);
        });
    }

    $scope.add = function(url) {
        mpdPlaylist.add({file: url}, $scope.refresh);
        $scope.refresh();
        $scope.addNewUrl = '';
    }

    $scope.playlistLoad = function(name) {
        console.log(name);
    }

    $scope.refreshCycle(10000);
});
