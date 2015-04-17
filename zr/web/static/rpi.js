var rpiApp = angular.module('RpiApp', ['ngResource']);


rpiApp.controller('MPDCtrl', function ($scope, $resource, $timeout) {
    $scope.status = {};
    $scope.playlist = [];

    var mpdPlaylist = $resource('/mpd/playlist', {}, {
        list: {isArray: true},
        add: {method: 'POST', isArray: true}
    });


    $scope.statusRefresh = function() {
        var mpdStatus = $resource('/mpd');
        mpdStatus.get(function (res) {
            $scope.status = res;
        });
    }

    $scope.playlistRefresh = function() {
        mpdPlaylist.list(function (res) {
            $scope.playlist = res;
        });
    }

    $scope.refresh = function() {
        $scope.statusRefresh();
        $scope.playlistRefresh();
        $timeout($scope.refresh, 10000);
    }

    $scope.play = function(id) {
        var mpdPlaylistSong = $resource('/mpd/playlist/:id',
            {id: id},
            {play: {method: 'PUT'}}
        );

        mpdPlaylistSong.play({action: 'play'}, $scope.refresh);
    }

    $scope.add = function(url) {
        mpdPlaylist.add({file: url}, $scope.refresh);
    }

    $scope.playlistLoad = function(name) {
        console.log(name);
    }

    $scope.refresh();
});
