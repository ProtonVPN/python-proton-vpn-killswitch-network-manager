%define unmangled_name proton-vpn-killswitch-network-manager
%define version 0.4.1
%define release 1

Prefix: %{_prefix}

Name: python3-%{unmangled_name}
Version: %{version}
Release: %{release}%{?dist}
Summary: %{unmangled_name} library

Group: ProtonVPN
License: GPLv3
Vendor: Proton Technologies AG <opensource@proton.me>
URL: https://github.com/ProtonVPN/%{unmangled_name}
Source0: %{unmangled_name}-%{version}.tar.gz
BuildArch: noarch
BuildRoot: %{_tmppath}/%{unmangled_name}-%{version}-%{release}-buildroot

BuildRequires: python3-proton-vpn-killswitch
BuildRequires: python3-proton-vpn-logger
BuildRequires: python3-setuptools
BuildRequires: python3-gobject
BuildRequires: NetworkManager

Requires: python3-proton-vpn-killswitch
Requires: python3-proton-vpn-logger
Requires: python3-gobject
Requires: NetworkManager

%{?python_disable_dependency_generator}

%description
Package %{unmangled_name} library.


%prep
%setup -n %{unmangled_name}-%{version} -n %{unmangled_name}-%{version}

%build
python3 setup.py build

%install
python3 setup.py install --single-version-externally-managed -O1 --root=$RPM_BUILD_ROOT --record=INSTALLED_FILES


%files -f INSTALLED_FILES
%{python3_sitelib}/proton/
%{python3_sitelib}/proton_vpn_killswitch_network_manager-%{version}*.egg-info/
%defattr(-,root,root)

%changelog
* Tue Feb 20 2024 Josep Llaneras <josep.llaneras@proton.ch> 0.4.1
- Fix switching between non-permanent and permanent KS

* Thu Feb 08 2024 Josep Llaneras <josep.llaneras@proton.ch> 0.4.0
- Add permanent kill switch

* Wed Feb 07 2024 Josep Llaneras <josep.llaneras@proton.ch> 0.3.0
- Wait for target interface state when adding/removing NM connections

* Mon Sep 04 2023 Alexandru Cheltuitor <alexandru.cheltuitor@proton.ch> 0.2.0
- Implement kill switch

* Tue Apr 04 2023 Alexandru Cheltuitor <alexandru.cheltuitor@proton.ch> 0.1.1
- Rely on NMClient for connection handling

* Thu Mar 23 2023 Alexandru Cheltuitor <alexandru.cheltuitor@proton.ch> 0.1.0
- Implement IPv6 leak protection

* Wed Jun 1 2022 Proton Technologies AG <opensource@proton.me> 0.0.1
- First RPM release
