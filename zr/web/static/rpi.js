var rpiApp = angular.module('RpiApp', ['ngResource']);


rpiApp.controller('MPDCtrl', function ($scope, $resource, $timeout) {
    $scope.settings = {'playlists': {}};
    $scope.status = {};
    $scope.playlist = [];

    var mpdSettings = $resource('/mpd/settings', {}, {
        get: {method: 'get'}
    });

    var mpdResource = $resource('/mpd', {}, {
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

    $scope.sendAction = function (action, callback) {
        mpdResource.send({'action': action}, callback);
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

    $scope.addPlaylist = function(urls) {
        $scope.sendAction('clear', function () {
            urls.forEach(function (url) {
                mpdPlaylist.add({file: url});
            })
            $timeout($scope.refresh, 1000);
            $timeout($scope.refresh, 2000);
            $timeout($scope.refresh, 5000);
        })

    }

    $scope.refreshCycle(10000);
    mpdSettings.get(function (res) {
        $scope.settings = res;
    })
});
